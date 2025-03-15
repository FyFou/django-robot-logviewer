"""
Package pour parser les fichiers MDF (Measurement Data Format).
Fournit des implémentations basées sur mdfreader et asammdf avec détection automatique.
"""

from .parser import MDFParser

__all__ = ['MDFParser']
