"""
Module pour parser les fichiers MDF (Measurement Data Format).
Ce module est désormais un simple wrapper autour du package mdf_parsers plus modulaire.
"""

from .mdf_parsers import MDFParser

# Re-export la classe MDFParser pour maintenir la compatibilité avec le code existant
__all__ = ['MDFParser']
