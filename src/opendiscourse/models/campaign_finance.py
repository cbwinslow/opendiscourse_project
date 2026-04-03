from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import relationship
import hashlib
from opendiscourse.database import Base


class UniversalIDMixin:
    """Mixin to add universal ID field computed from natural key fields."""

    universal_id = Column(String(64), unique=True, nullable=False)

    def _compute_universal_id(self, *key_components: str) -> str:
        """Compute universal ID from key components using SHA-256."""
        key_string = "|".join(str(component) for component in key_components if component is not None)
        return hashlib.sha256(key_string.encode("utf-8")).hexdigest()[:32]

    def generate_universal_id(self):
        """Override in subclasses to generate universal ID from natural keys."""
        raise NotImplementedError("Subclasses must implement generate_universal_id")


class FECCandidate(UniversalIDMixin, Base):
    __tablename__ = "fec_candidates"

    id = Column(Integer, primary_key=True)
    fec_candidate_id = Column(String(20), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    party = Column(String(50))
    office_sought = Column(String(50))
    state = Column(String(50))
    district = Column(Integer)
    incumbent_active = Column(String(1))
    principal_committee_id = Column(String(20))
    election_year = Column(Integer)
    election_status = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def generate_universal_id(self):
        """Generate universal ID from FEC candidate ID."""
        self.universal_id = self._compute_universal_id("fec_candidate", self.fec_candidate_id)


class FECCommittee(UniversalIDMixin, Base):
    __tablename__ = "fec_committees"

    id = Column(Integer, primary_key=True)
    fec_committee_id = Column(String(20), unique=True, nullable=False)
    name = Column(String(300), nullable=False)
    committee_type = Column(String(50))
    committee_designation = Column(String(50))
    party = Column(String(50))
    treasurer_name = Column(String(200))
    street1 = Column(String(100))
    street2 = Column(String(100))
    city = Column(String(100))
    state = Column(String(50))
    zip = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def generate_universal_id(self):
        """Generate universal ID from FEC committee ID."""
        self.universal_id = self._compute_universal_id("fec_committee", self.fec_committee_id)


class FECCommitteeCandidate(Base):
    __tablename__ = "fec_committee_candidates"

    id = Column(Integer, primary_key=True)
    fec_committee_id = Column(String(20))
    fec_candidate_id = Column(String(20))
    election_year = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())


class FECContribution(Base):
    __tablename__ = "fec_contributions"

    id = Column(Integer, primary_key=True)
    filing_id = Column(Integer)
    report_year = Column(Integer)
    report_type = Column(String(50))
    committee_id = Column(String(20), ForeignKey("fec_committees.fec_committee_id"))
    contributor_name = Column(String(200))
    contributor_city = Column(String(100))
    contributor_state = Column(String(50))
    contributor_zip = Column(String(20))
    employer = Column(String(200))
    occupation = Column(String(200))
    contribution_date = Column(Date, nullable=False)
    contribution_amount = Column(Numeric(12, 2), nullable=False)
    contribution_type = Column(String(50))
    memo_code = Column(String(1))
    memo_text = Column(Text)
    election_type = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())


class FECDisbursement(Base):
    __tablename__ = "fec_disbursements"

    id = Column(Integer, primary_key=True)
    filing_id = Column(Integer)
    report_year = Column(Integer)
    committee_id = Column(String(20), ForeignKey("fec_committees.fec_committee_id"))
    payee_name = Column(String(200))
    payee_city = Column(String(100))
    payee_state = Column(String(50))
    payee_zip = Column(String(20))
    disbursement_date = Column(Date, nullable=False)
    disbursement_amount = Column(Numeric(12, 2), nullable=False)
    disbursement_type = Column(String(50))
    purpose = Column(String(200))
    category = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())


class FECIndependentExpenditure(Base):
    __tablename__ = "fec_independent_expenditures"

    id = Column(Integer, primary_key=True)
    filing_id = Column(Integer)
    committee_id = Column(String(20), ForeignKey("fec_committees.fec_committee_id"))
    candidate_id = Column(String(20), ForeignKey("fec_candidates.fec_candidate_id"))
    support_oppose = Column(String(10))
    expenditure_date = Column(Date, nullable=False)
    expenditure_amount = Column(Numeric(12, 2), nullable=False)
    expenditure_type = Column(String(50))
    memo_code = Column(String(1))
    memo_text = Column(Text)
    candidate_office = Column(String(20))
    candidate_state = Column(String(50))
    candidate_district = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())


class FECFiling(Base):
    __tablename__ = "fec_filings"

    id = Column(Integer, primary_key=True)
    filing_number = Column(Integer, unique=True, nullable=False)
    committee_id = Column(String(20), ForeignKey("fec_committees.fec_committee_id"))
    report_type = Column(String(50))
    report_year = Column(Integer)
    coverage_start = Column(Date)
    coverage_end = Column(Date)
    receipt_date = Column(Date)
    filing_status = Column(String(50))
    pdf_url = Column(Text)
    xml_url = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class FECTotal(Base):
    __tablename__ = "fec_totals"

    id = Column(Integer, primary_key=True)
    committee_id = Column(String(20), ForeignKey("fec_committees.fec_committee_id"))
    report_year = Column(Integer)
    report_type = Column(String(50))
    receipts = Column(Numeric(14, 2))
    disbursements = Column(Numeric(14, 2))
    cash_on_hand = Column(Numeric(14, 2))
    debt_owed = Column(Numeric(14, 2))
    individual_contributions = Column(Numeric(14, 2))
    pac_contributions = Column(Numeric(14, 2))
    candidate_contributions = Column(Numeric(14, 2))
    created_at = Column(DateTime, server_default=func.now())
