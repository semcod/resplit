"""
rebuild plugin system.

Plugins are discovered via Python package entry points:

  [project.entry-points."rebuild.scanners"]
  my_scanner = "my_package.scanners:MyScanner"

  [project.entry-points."rebuild.reporters"]
  my_reporter = "my_package.reporters:MyReporter"

Built-in groups:
  rebuild.scanners  — classes with .scan(path) -> list[ScanResult]
  rebuild.reporters — classes with .report(results, output_dir) -> None
"""

from .registry import PluginRegistry, load_plugins

__all__ = ["PluginRegistry", "load_plugins"]
