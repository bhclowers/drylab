"""Diagnostics: capture errors for display in the UI *and* the terminal.

marimo ships ``show_tracebacks: false`` in app mode, so a failing cell renders
as an empty output and the student sees nothing. Someone running the notebook
from a terminal sees the traceback; someone using the hosted WASM build never
does. This module records failures so they can be shown in-app, while also
mirroring them to stderr so terminal users get the usual stream.

Design notes:

* The log is **bounded** and **deduplicating**. marimo re-runs cells whenever
  a dependency changes, so a persistent error would otherwise append on every
  keystroke; repeats increment a count instead of adding entries.
* Records carry the full traceback, but the summary shown first is the
  exception message -- a student needs "what went wrong", with the traceback
  available underneath rather than in their face.
* Nothing here is global: a log is an object the caller owns.
"""

from __future__ import annotations

import sys
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator

__all__ = ["DiagnosticRecord", "DiagnosticsLog"]

#: Default cap on retained records; oldest are dropped first.
DEFAULT_MAX_RECORDS = 50


@dataclass
class DiagnosticRecord:
    """One captured failure (or note), with provenance and repeat count."""

    context: str
    kind: str
    message: str
    traceback_text: str = ""
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    count: int = 1

    @property
    def signature(self) -> tuple[str, str, str]:
        """Identity used for deduplication."""
        return (self.context, self.kind, self.message)

    def summary(self) -> str:
        stamp = self.last_seen.strftime("%H:%M:%S")
        repeat = f" (x{self.count})" if self.count > 1 else ""
        return f"[{stamp}] {self.context}: {self.kind}: {self.message}{repeat}"


class DiagnosticsLog:
    """A bounded, deduplicating record of failures.

    Not thread-safe; a notebook session is single-threaded per cell run.
    """

    def __init__(
        self, max_records: int = DEFAULT_MAX_RECORDS, mirror_to_stderr: bool = True
    ):
        if max_records < 1:
            raise ValueError(f"max_records must be >= 1, got {max_records}")
        self.max_records = max_records
        self.mirror_to_stderr = mirror_to_stderr
        self._records: list[DiagnosticRecord] = []

    @property
    def records(self) -> tuple[DiagnosticRecord, ...]:
        """Most recent first."""
        return tuple(sorted(self._records, key=lambda r: r.last_seen, reverse=True))

    def __len__(self) -> int:
        return len(self._records)

    def clear(self) -> None:
        self._records.clear()

    def record(
        self,
        context: str,
        exc: BaseException | None = None,
        *,
        kind: str | None = None,
        message: str | None = None,
    ) -> DiagnosticRecord:
        """Add a failure. Either an exception or an explicit kind+message."""
        if exc is not None:
            resolved_kind = kind or type(exc).__name__
            resolved_message = message or str(exc)
            tb = "".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)
            )
        else:
            if kind is None or message is None:
                raise ValueError(
                    "record() needs either an exception or both kind and message"
                )
            resolved_kind, resolved_message, tb = kind, message, ""

        new = DiagnosticRecord(
            context=context,
            kind=resolved_kind,
            message=resolved_message,
            traceback_text=tb,
        )
        for existing in self._records:
            if existing.signature == new.signature:
                existing.count += 1
                existing.last_seen = new.last_seen
                if tb:
                    existing.traceback_text = tb
                self._emit(existing)
                return existing

        self._records.append(new)
        # Bound the log: drop the oldest by last_seen.
        while len(self._records) > self.max_records:
            oldest = min(self._records, key=lambda r: r.last_seen)
            self._records.remove(oldest)
        self._emit(new)
        return new

    def _emit(self, rec: DiagnosticRecord) -> None:
        """Mirror to stderr so terminal users see it in the usual place."""
        if not self.mirror_to_stderr:
            return
        print(f"[drylab] {rec.summary()}", file=sys.stderr)
        if rec.traceback_text and rec.count == 1:
            print(rec.traceback_text, file=sys.stderr, end="")

    @contextmanager
    def capture(
        self, context: str, reraise: bool = False
    ) -> Iterator[list[BaseException]]:
        """Run a block, recording any exception instead of losing it.

        Yields a list that receives the exception if one occurred, so the
        caller can branch on failure without re-catching::

            with log.capture("gradient") as failed:
                results = compute(inputs)
            if failed:
                ...

        The exception is recorded and, unless ``reraise``, suppressed -- an
        explicit, visible decision rather than a silent pass.
        """
        failures: list[BaseException] = []
        try:
            yield failures
        except Exception as e:  # noqa: BLE001 - deliberately broad; it is recorded
            failures.append(e)
            self.record(context, e)
            if reraise:
                raise
