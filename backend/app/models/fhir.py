from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FHIRResource(BaseModel):
    """Base model for FHIR resources used by the application."""

    model_config = ConfigDict(extra="allow")

    resourceType: str
    id: str


class FHIRBundleEntry(BaseModel):
    """A single entry in a FHIR Bundle."""

    model_config = ConfigDict(extra="allow")

    resource: dict[str, Any]


class FHIRBundle(BaseModel):
    """FHIR Bundle containing the resources used by the snapshot."""

    model_config = ConfigDict(extra="allow")

    resourceType: str
    id: str
    type: str
    entry: list[FHIRBundleEntry]


class FHIRIdentifier(BaseModel):
    model_config = ConfigDict(extra="allow")

    system: str | None = None
    value: str | None = None


class FHIRHumanName(BaseModel):
    model_config = ConfigDict(extra="allow")

    family: str | None = None
    given: list[str] | None = None


class FHIRContactPoint(BaseModel):
    model_config = ConfigDict(extra="allow")

    system: str | None = None
    value: str | None = None
    use: str | None = None


class FHIRAddress(BaseModel):
    model_config = ConfigDict(extra="allow")

    line: list[str] | None = None
    city: str | None = None
    state: str | None = None
    postalCode: str | None = None


class FHIRPatient(FHIRResource):
    """FHIR Patient fields needed for the clinical snapshot."""

    identifier: list[FHIRIdentifier] | None = None
    name: list[FHIRHumanName] | None = None
    telecom: list[FHIRContactPoint] | None = None
    gender: str | None = None
    birthDate: str | None = None
    address: list[FHIRAddress] | None = None
    active: bool | None = None


class FHIRCoding(BaseModel):
    """FHIR coding information."""

    model_config = ConfigDict(extra="allow")

    system: str | None = None
    code: str | None = None
    display: str | None = None


class FHIRCodeableConcept(BaseModel):
    """FHIR CodeableConcept containing one or more codings."""

    model_config = ConfigDict(extra="allow")

    coding: list[FHIRCoding] | None = None
    text: str | None = None


class FHIRReference(BaseModel):
    """FHIR reference to another resource."""

    model_config = ConfigDict(extra="allow")

    reference: str | None = None
    display: str | None = None


class FHIRCondition(FHIRResource):
    """FHIR Condition fields needed for the clinical snapshot."""

    clinicalStatus: FHIRCodeableConcept | None = None
    verificationStatus: FHIRCodeableConcept | None = None
    code: FHIRCodeableConcept | None = None
    subject: FHIRReference | None = None
    encounter: FHIRReference | None = None
    onsetDateTime: str | None = None


class FHIRPeriod(BaseModel):
    """FHIR Period with potentially partial date/time values."""

    model_config = ConfigDict(extra="allow")

    start: str | None = None
    end: str | None = None


class FHIREncounter(FHIRResource):
    """FHIR Encounter fields needed for the clinical snapshot."""

    status: str | None = None
    class_: dict[str, Any] | None = Field(default=None, alias="class")
    type: list[FHIRCodeableConcept] | None = None
    subject: FHIRReference | None = None
    period: FHIRPeriod | None = None


class FHIRQuantity(BaseModel):
    """FHIR Quantity."""

    model_config = ConfigDict(extra="allow")

    value: float | None = None
    unit: str | None = None
    system: str | None = None
    code: str | None = None


class FHIRObservationComponent(BaseModel):
    """A component of a FHIR Observation."""

    model_config = ConfigDict(extra="allow")

    code: FHIRCodeableConcept
    valueQuantity: FHIRQuantity | None = None


class FHIRObservation(FHIRResource):
    """FHIR Observation fields needed for the clinical snapshot."""

    status: str | None = None
    category: list[FHIRCodeableConcept] | None = None
    code: FHIRCodeableConcept | None = None
    subject: FHIRReference | None = None
    encounter: FHIRReference | None = None
    performer: list[FHIRReference] | None = None
    effectiveDateTime: str | None = None
    valueQuantity: FHIRQuantity | None = None
    component: list[FHIRObservationComponent] | None = None


class FHIRDosage(BaseModel):
    """A single dosage instruction entry."""

    model_config = ConfigDict(extra="allow")

    text: str | None = None


class FHIRMedicationRequest(FHIRResource):
    """FHIR MedicationRequest fields needed for the clinical snapshot."""

    status: str | None = None
    intent: str | None = None
    medicationCodeableConcept: FHIRCodeableConcept | None = None
    subject: FHIRReference | None = None
    encounter: FHIRReference | None = None
    authoredOn: str | None = None
    dosageInstruction: list[FHIRDosage] | None = None


class FHIRAllergyIntolerance(FHIRResource):
    """FHIR AllergyIntolerance fields needed for the clinical snapshot."""

    clinicalStatus: FHIRCodeableConcept | None = None
    verificationStatus: FHIRCodeableConcept | None = None
    code: FHIRCodeableConcept | None = None
    criticality: str | None = None
    patient: FHIRReference | None = None
    recordedDate: str | None = None