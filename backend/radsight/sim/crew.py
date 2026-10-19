"""Simulated crew: roster, EVA plans and the response policy.

Crew names and doses are fictional. Each astronaut carries a simulated
active dosimeter: true dose x (1 + bias) + small Gaussian noise, the way two
real dosimeters never quite agree.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass(frozen=True)
class CrewMember:
    id: str
    name: str
    role: str
    agency: str
    base: str                    # "orbit" or "surface"
    prior_career_mSv: float      # dose from earlier missions
    dosimeter_bias: float


CREW: list[CrewMember] = [
    CrewMember("ruiz", "Elena Ruiz", "Commander", "ESA", "orbit", 112.0, 0.02),
    CrewMember("okafor", "Marcus Okafor", "Pilot", "NASA", "orbit", 48.0, -0.015),
    CrewMember("tanaka", "Aiko Tanaka", "Mission Specialist", "JAXA", "surface", 76.0, 0.01),
    CrewMember("lindqvist", "Jonas Lindqvist", "Mission Specialist", "ESA", "surface", 19.0, -0.025),
]

NOMINAL = {"orbit": "cabin", "surface": "habitat"}
EVA = {"orbit": "eva", "surface": "surface_eva"}
SHELTER = {"orbit": "shelter", "surface": "surface_shelter"}


@dataclass
class EvaWindow:
    crew_ids: tuple[str, ...]
    start: datetime
    end: datetime
    label: str = "EVA"


@dataclass
class Policy:
    """How the crew responds to radiation information.

    radsight     shelter as soon as the status reaches Action Needed (which the
                 imminent-event detector can raise before protons arrive);
                 no new EVA starts unless the status is Safe.
    conventional no early warning: shelter once >=10 MeV flux has stayed at
                 S2 (100 pfu) for an hour; EVAs only stop at S1 (10 pfu).
    """
    name: str
    eva_ingress_min: float = 30.0
    cabin_move_min: float = 10.0
    decision_delay_min: float = 0.0


RADSIGHT = Policy("radsight")
CONVENTIONAL = Policy("conventional", decision_delay_min=60.0)


@dataclass
class CrewState:
    location: str
    in_shelter: bool = False
    move_at: datetime | None = None
    danger_since: datetime | None = None
    cancelled: set = field(default_factory=set)   # indexes of EVA windows cancelled


def step_crew(member: CrewMember, state: CrewState, t: datetime, policy: Policy,
              status: str, j10: float, windows: list[EvaWindow]) -> list[str]:
    """Advance one crew member by one time step; returns event messages."""
    events: list[str] = []
    if policy.name == "radsight":
        danger = status == "action"
        no_new_eva = status != "safe"
    else:
        danger = j10 >= 100
        no_new_eva = j10 >= 10

    if danger:
        state.danger_since = state.danger_since or t
    else:
        state.danger_since = None

    on_eva = state.location == EVA[member.base]
    decided = danger and (t - state.danger_since) >= timedelta(minutes=policy.decision_delay_min)

    if decided and not state.in_shelter and state.move_at is None:
        delay = policy.eva_ingress_min if on_eva else policy.cabin_move_min
        state.move_at = t + timedelta(minutes=delay)
        if on_eva:
            events.append(f"{member.name} aborts EVA, ingress started")
    if not danger:
        state.move_at = None
        if state.in_shelter:
            state.in_shelter = False
            events.append(f"{member.name} leaves the shelter")
    if state.move_at is not None and t >= state.move_at:
        state.in_shelter, state.move_at = True, None
        events.append(f"{member.name} reaches the storm shelter")

    if state.in_shelter:
        loc = SHELTER[member.base]
    elif state.move_at is not None and on_eva:
        loc = EVA[member.base]  # still walking back
    else:
        loc = NOMINAL[member.base]
        for k, w in enumerate(windows):
            if member.id not in w.crew_ids or k in state.cancelled or not (w.start <= t < w.end):
                continue
            if on_eva:
                loc = EVA[member.base]
            elif no_new_eva:
                state.cancelled.add(k)
                events.append(f"{w.label} for {member.name} postponed")
            else:
                loc = EVA[member.base]
                events.append(f"{member.name} starts {w.label}")
            break
    if on_eva and loc != EVA[member.base] and not state.in_shelter:
        events.append(f"{member.name} back inside")
    state.location = loc
    return events
