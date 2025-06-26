from fastapi import FastAPI, HTTPException, Path, Query, Body, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from uuid import uuid4, UUID
from datetime import datetime

app = FastAPI(
    title="Event Manager Backend",
    description=(
        "Handles core event management logic, APIs, and data processing for "
        "events, attendees, and scheduling."
    ),
    version="1.0.0",
    openapi_tags=[
        {"name": "Events", "description": "Operations with events."},
        {"name": "Attendees", "description": "Operations with attendees."},
        {"name": "Scheduling", "description": "Event scheduling and attendee management."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for demo purposes (replace with actual DB in production)
EVENTS_DB: Dict[UUID, Dict] = {}
ATTENDEES_DB: Dict[UUID, Dict] = {}

# ==== MODELS ====


class AttendeeBase(BaseModel):
    name: str = Field(..., description="Full name of the attendee")
    email: str = Field(..., description="Email address of the attendee")


class AttendeeCreate(AttendeeBase):
    pass


class AttendeeUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Updated full name of the attendee")
    email: Optional[str] = Field(None, description="Updated email address of the attendee")


class Attendee(AttendeeBase):
    id: UUID = Field(..., description="Unique identifier for the attendee")

    class Config:
        orm_mode = True


class EventBase(BaseModel):
    title: str = Field(..., description="Title or name of the event")
    description: Optional[str] = Field(None, description="Detailed description of the event")
    location: Optional[str] = Field(None, description="Location of the event")
    start_time: datetime = Field(..., description="Start time of the event")
    end_time: datetime = Field(..., description="End time of the event")


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Updated event title")
    description: Optional[str] = Field(None, description="Updated event description")
    location: Optional[str] = Field(None, description="Updated location")
    start_time: Optional[datetime] = Field(None, description="Updated start time")
    end_time: Optional[datetime] = Field(None, description="Updated end time")


class Event(EventBase):
    id: UUID = Field(..., description="Unique identifier for the event")
    attendees: List[UUID] = Field(
        default_factory=list,
        description="List of attendee IDs assigned to the event"
    )

    class Config:
        orm_mode = True


# ==== API ENDPOINTS ====


@app.get("/", tags=["Health"])
# PUBLIC_INTERFACE
def health_check():
    """Check the health of the API.
    Returns a simple healthy message for readiness/liveness probe.
    """
    return {"message": "Healthy"}


# ==== EVENT ENDPOINTS ====


@app.post(
    "/events/",
    response_model=Event,
    status_code=status.HTTP_201_CREATED,
    tags=["Events"],
    summary="Create a new event",
    description="Create a new event with the provided details.",
)
# PUBLIC_INTERFACE
def create_event(event_data: EventCreate = Body(..., description="Event details to create")):
    """Create a new event."""
    event_id = uuid4()
    event = event_data.dict()
    event["id"] = event_id
    event["attendees"] = []
    EVENTS_DB[event_id] = event
    return Event(**event)


@app.get(
    "/events/",
    response_model=List[Event],
    tags=["Events"],
    summary="List all events",
    description="Retrieve a list of all events."
)
# PUBLIC_INTERFACE
def list_events(skip: int = Query(0, ge=0), limit: int = Query(100, le=1000)):
    """List all events with pagination."""
    events = list(EVENTS_DB.values())
    return [Event(**e) for e in events[skip: skip + limit]]


@app.get(
    "/events/{event_id}",
    response_model=Event,
    tags=["Events"],
    summary="Get a specific event",
    description="Retrieve a single event by its unique ID.",
)
# PUBLIC_INTERFACE
def get_event(event_id: UUID = Path(..., description="ID of the event")):
    """Get a single event by ID."""
    event = EVENTS_DB.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return Event(**event)


@app.put(
    "/events/{event_id}",
    response_model=Event,
    tags=["Events"],
    summary="Update an event",
    description="Update properties of an existing event.",
)
# PUBLIC_INTERFACE
def update_event(
    event_id: UUID = Path(..., description="ID of the event"),
    update_data: EventUpdate = Body(..., description="Fields to update")
):
    """Update an existing event."""
    event = EVENTS_DB.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    update_dict = update_data.dict(exclude_unset=True)
    for k, v in update_dict.items():
        event[k] = v
    EVENTS_DB[event_id] = event
    return Event(**event)


@app.delete(
    "/events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Events"],
    summary="Delete an event",
    description="Delete an event by its unique ID.",
)
# PUBLIC_INTERFACE
def delete_event(event_id: UUID = Path(..., description="ID of the event to delete")):
    """Delete an event."""
    if event_id not in EVENTS_DB:
        raise HTTPException(status_code=404, detail="Event not found")
    del EVENTS_DB[event_id]
    return None


# ==== ATTENDEE ENDPOINTS ====


@app.post(
    "/attendees/",
    response_model=Attendee,
    status_code=status.HTTP_201_CREATED,
    tags=["Attendees"],
    summary="Create an attendee",
    description="Create a new attendee and add to the system.",
)
# PUBLIC_INTERFACE
def create_attendee(attendee_data: AttendeeCreate = Body(..., description="Attendee details")):
    """Create a new attendee."""
    attendee_id = uuid4()
    attendee = attendee_data.dict()
    attendee["id"] = attendee_id
    ATTENDEES_DB[attendee_id] = attendee
    return Attendee(**attendee)


@app.get(
    "/attendees/",
    response_model=List[Attendee],
    tags=["Attendees"],
    summary="List all attendees",
    description="Retrieve a list of all attendees.",
)
# PUBLIC_INTERFACE
def list_attendees(skip: int = Query(0, ge=0), limit: int = Query(100, le=1000)):
    """List all attendees with pagination."""
    attendees = list(ATTENDEES_DB.values())
    return [Attendee(**a) for a in attendees[skip: skip + limit]]


@app.get(
    "/attendees/{attendee_id}",
    response_model=Attendee,
    tags=["Attendees"],
    summary="Get an attendee",
    description="Retrieve an attendee by their unique ID.",
)
# PUBLIC_INTERFACE
def get_attendee(attendee_id: UUID = Path(..., description="ID of the attendee")):
    """Get details for a single attendee."""
    attendee = ATTENDEES_DB.get(attendee_id)
    if not attendee:
        raise HTTPException(status_code=404, detail="Attendee not found")
    return Attendee(**attendee)


@app.put(
    "/attendees/{attendee_id}",
    response_model=Attendee,
    tags=["Attendees"],
    summary="Update an attendee",
    description="Update details for an existing attendee.",
)
# PUBLIC_INTERFACE
def update_attendee(
    attendee_id: UUID = Path(..., description="ID of the attendee"),
    update_data: AttendeeUpdate = Body(..., description="Fields to update")
):
    """Update details of an attendee."""
    attendee = ATTENDEES_DB.get(attendee_id)
    if not attendee:
        raise HTTPException(status_code=404, detail="Attendee not found")
    update_dict = update_data.dict(exclude_unset=True)
    for k, v in update_dict.items():
        attendee[k] = v
    ATTENDEES_DB[attendee_id] = attendee
    return Attendee(**attendee)


@app.delete(
    "/attendees/{attendee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Attendees"],
    summary="Delete an attendee",
    description="Delete an attendee by their unique ID.",
)
# PUBLIC_INTERFACE
def delete_attendee(attendee_id: UUID = Path(..., description="ID of the attendee to delete")):
    """Delete an attendee."""
    if attendee_id not in ATTENDEES_DB:
        raise HTTPException(status_code=404, detail="Attendee not found")
    # Also remove attendee from any events
    for event in EVENTS_DB.values():
        if attendee_id in event["attendees"]:
            event["attendees"].remove(attendee_id)
    del ATTENDEES_DB[attendee_id]
    return None


# ==== SCHEDULING ====


@app.post(
    "/events/{event_id}/attendees/{attendee_id}",
    status_code=status.HTTP_200_OK,
    tags=["Scheduling"],
    summary="Assign attendee to an event",
    description="Add an attendee to a particular event.",
)
# PUBLIC_INTERFACE
def assign_attendee_to_event(
    event_id: UUID = Path(..., description="ID of the event"),
    attendee_id: UUID = Path(..., description="ID of the attendee")
):
    """Assign an attendee to an event."""
    event = EVENTS_DB.get(event_id)
    attendee = ATTENDEES_DB.get(attendee_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if not attendee:
        raise HTTPException(status_code=404, detail="Attendee not found")
    if attendee_id in event["attendees"]:
        raise HTTPException(status_code=400, detail="Attendee already assigned to event")
    event["attendees"].append(attendee_id)
    return {"message": f"Attendee {attendee_id} assigned to event {event_id}"}


@app.delete(
    "/events/{event_id}/attendees/{attendee_id}",
    status_code=status.HTTP_200_OK,
    tags=["Scheduling"],
    summary="Remove attendee from event",
    description="Remove (un-assign) an attendee from an event.",
)
# PUBLIC_INTERFACE
def remove_attendee_from_event(
    event_id: UUID = Path(..., description="ID of the event"),
    attendee_id: UUID = Path(..., description="ID of the attendee to unassign")
):
    """Remove (un-assign) an attendee from an event."""
    event = EVENTS_DB.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if attendee_id not in event["attendees"]:
        raise HTTPException(status_code=404, detail="Attendee not assigned to event")
    event["attendees"].remove(attendee_id)
    return {"message": f"Attendee {attendee_id} removed from event {event_id}"}


@app.get(
    "/events/{event_id}/attendees/",
    response_model=List[Attendee],
    status_code=status.HTTP_200_OK,
    tags=["Scheduling"],
    summary="List attendees for an event",
    description="List all attendees assigned to a given event",
)
# PUBLIC_INTERFACE
def list_attendees_for_event(
    event_id: UUID = Path(..., description="ID of the event")
):
    """List all attendees for a particular event."""
    event = EVENTS_DB.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    attendee_ids = event["attendees"]
    attendees = []
    for aid in attendee_ids:
        attendee = ATTENDEES_DB.get(aid)
        if attendee:
            attendees.append(Attendee(**attendee))
    return attendees


@app.get(
    "/attendees/{attendee_id}/events/",
    response_model=List[Event],
    status_code=status.HTTP_200_OK,
    tags=["Scheduling"],
    summary="List events for an attendee",
    description="List all events an attendee is participating in.",
)
# PUBLIC_INTERFACE
def list_events_for_attendee(
    attendee_id: UUID = Path(..., description="ID of the attendee")
):
    """List all events for a particular attendee."""
    if attendee_id not in ATTENDEES_DB:
        raise HTTPException(status_code=404, detail="Attendee not found")
    event_list = []
    for event in EVENTS_DB.values():
        if attendee_id in event["attendees"]:
            event_list.append(Event(**event))
    return event_list
