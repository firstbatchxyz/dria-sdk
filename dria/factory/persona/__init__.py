from .random_vars import RandomVars
from .backstory import BackStory
from .short_bio import ShortBio

PersonaBackstory = [RandomVars, BackStory]
PersonaBio = [RandomVars, ShortBio]


__all__ = ["RandomVars", "BackStory", "PersonaBio", "PersonaBackstory"]
