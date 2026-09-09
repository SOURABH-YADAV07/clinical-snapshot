from pydantic import BaseModel, Field


class CodeDisplay(BaseModel):
    """A coding with an explicit flag for whether a display value is available."""

    system: str | None = None
    code: str | None = None
    display: str | None = None
    display_available: bool = True


class PatientSummary(BaseModel):
    id: str
    name: str | None = None
    birth_date: str | None = None
    gender: str | None = None
    phone: str | None = None
    address: str | None = None


class PatientListItem(BaseModel):
    id: str
    name: str | None = None
    birth_date: str | None = None
    phone: str | None = None
    is_canonical: bool = True
    note: str | None = None


class ProblemSummary(BaseModel):
    id: str
    code: CodeDisplay
    clinical_status: str | None = None
    verification_status: str | None = None
    onset: str | None = None
    encounter: "EncounterSummary | None" = None
    encounter_reference: str | None = None
    reference_resolved: bool = False
    uncertainty_notes: list[str] = Field(default_factory=list)


class MedicationSummary(BaseModel):
    id: str
    medication: CodeDisplay
    instructions: str | None = None
    authored_on: str | None = None
    status: str | None = None
    uncertainty_notes: list[str] = Field(default_factory=list)


class AllergySummary(BaseModel):
    id: str
    code: CodeDisplay
    clinical_status: str | None = None
    verification_status: str | None = None
    criticality: str | None = None
    uncertainty_notes: list[str] = Field(default_factory=list)


class EncounterSummary(BaseModel):
    id: str
    type: CodeDisplay | None = None
    status: str | None = None
    start: str | None = None
    end: str | None = None
    age_days_at_snapshot: int | None = None
    uncertainty_notes: list[str] = Field(default_factory=list)


class ObservationValue(BaseModel):
    code: CodeDisplay | None = None
    value: float | None = None
    unit: str | None = None


class ObservationSummary(BaseModel):
    id: str
    code: CodeDisplay
    values: list[ObservationValue] = Field(default_factory=list)
    effective: str | None = None
    encounter: EncounterSummary | None = None
    encounter_reference: str | None = None
    reference_resolved: bool = False
    uncertainty_notes: list[str] = Field(default_factory=list)


class DataQualityFlag(BaseModel):
    message: str
    resource_type: str | None = None
    resource_id: str | None = None


class PatientSummaryResponse(BaseModel):
    patient: PatientSummary
    problems: list[ProblemSummary] = Field(default_factory=list)
    medications: list[MedicationSummary] = Field(default_factory=list)
    allergies: list[AllergySummary] = Field(default_factory=list)
    encounters: list[EncounterSummary] = Field(default_factory=list)
    observations: list[ObservationSummary] = Field(default_factory=list)
    data_quality: list[DataQualityFlag] = Field(default_factory=list)


ProblemSummary.model_rebuild()
