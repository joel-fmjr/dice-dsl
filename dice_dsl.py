import random
from lark import Lark

parser = Lark.open("dice.lark", rel_to=__file__)