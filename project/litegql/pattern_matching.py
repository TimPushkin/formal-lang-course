from dataclasses import dataclass

from project.litegql.types.base_type import BaseType
from project.litegql.types.lgql_edge import Edge
from project.litegql.types.lgql_pair import Pair


@dataclass
class Pattern:
    pass


@dataclass
class Wildcard(Pattern):
    pass


@dataclass
class Name(Pattern):
    name: str


@dataclass
class Unpair(Pattern):
    fst: Pattern
    snd: Pattern


@dataclass
class Unedge(Pattern):
    st: Pattern
    lab: Wildcard | Name
    fn: Pattern


def match(pat: Pattern, value: BaseType) -> dict[str, BaseType]:
    match [pat, value]:
        case [Wildcard(), _]:
            return {}
        case [Name(name), _]:
            return {name: value}
        case [Unpair(fst_pat, snd_pat), Pair(fst=fst, snd=snd)]:
            fst_match = match(fst_pat, fst)
            snd_match = match(snd_pat, snd)
            return fst_match | snd_match
        case [Unedge(st_pat, lab_pat, fn_pat), Edge(st=st, lab=lab, fn=fn)]:
            fst_match = match(st_pat, st)
            lab_pat = match(lab_pat, lab)
            snd_match = match(fn_pat, fn)
            return fst_match | lab_pat | snd_match
        case _:
            raise ValueError(f"Cannot match {pat} against {value.meta}")
