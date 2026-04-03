from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, Time, UniqueConstraint, func
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


class Congress(Base):
    __tablename__ = "congresses"

    id = Column(Integer, primary_key=True)
    congress_number = Column(Integer, unique=True, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Chamber(Base):
    __tablename__ = "chambers"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)
    name = Column(String(50), nullable=False)


class Member(UniversalIDMixin, Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True)
    bioguide_id = Column(String(20), unique=True)
    govtrack_id = Column(Integer, unique=True)
    thomas_id = Column(String(20))
    lis_id = Column(String(20))
    fec_id = Column(String(20))
    opensecrets_id = Column(String(20))
    vote_smart_id = Column(Integer)
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    last_name = Column(String(100), nullable=False)
    suffix = Column(String(20))
    nickname = Column(String(100))
    full_name = Column(String(200))
    date_of_birth = Column(Date)
    gender = Column(String(20))
    party = Column(String(50))
    state = Column(String(50), nullable=False)
    district = Column(Integer)
    chamber = Column(String(20))
    title = Column(String(50))
    website_url = Column(Text)
    contact_form_url = Column(Text)
    phone = Column(String(30))
    office_address = Column(Text)
    rss_url = Column(Text)
    twitter_id = Column(String(100))
    youtube_id = Column(String(100))
    facebook_id = Column(String(100))
    image_url = Column(Text)
    is_current = Column(Boolean, default=True)
    first_congress = Column(Integer)
    last_congress = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def generate_universal_id(self):
        """Generate universal ID from bioguide_id or other stable identifiers."""
        if self.bioguide_id:
            self.universal_id = self._compute_universal_id("member", "bioguide", self.bioguide_id)
        elif self.govtrack_id:
            self.universal_id = self._compute_universal_id("member", "govtrack", str(self.govtrack_id))
        else:
            # Fallback to name-based ID (less stable)
            self.universal_id = self._compute_universal_id(
                "member", "name", self.first_name, self.last_name, str(self.date_of_birth)
            )

    terms = relationship("MemberTerm", back_populates="member")
    sponsored_bills = relationship("Bill", back_populates="sponsor", foreign_keys="Bill.sponsor_id")


class MemberTerm(Base):
    __tablename__ = "member_terms"

    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    congress_id = Column(Integer, ForeignKey("congresses.id"))
    chamber = Column(String(20), nullable=False)
    state = Column(String(50), nullable=False)
    district = Column(Integer)
    party = Column(String(50), nullable=False)
    class_number = Column("class", Integer)
    state_rank = Column(String(10))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    how_ended = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())

    member = relationship("Member", back_populates="terms")


class Committee(Base):
    __tablename__ = "committees"

    id = Column(Integer, primary_key=True)
    congress_gov_id = Column(String(50), unique=True)
    house_committee_id = Column(String(20))
    senate_committee_id = Column(String(20))
    name = Column(String(200), nullable=False)
    chamber = Column(String(20))
    committee_type = Column(String(50))
    parent_committee_id = Column(Integer, ForeignKey("committees.id"))
    congress_id = Column(Integer, ForeignKey("congresses.id"))
    is_current = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    parent = relationship("Committee", remote_side=[id], backref="subcommittees")


class CommitteeMembership(Base):
    __tablename__ = "committee_memberships"

    id = Column(Integer, primary_key=True)
    committee_id = Column(Integer, ForeignKey("committees.id"))
    member_id = Column(Integer, ForeignKey("members.id"))
    congress_id = Column(Integer, ForeignKey("congresses.id"))
    role = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())


class Bill(UniversalIDMixin, Base):
    __tablename__ = "bills"
    __table_args__ = (UniqueConstraint("congress_id", "bill_type", "number"),)

    id = Column(Integer, primary_key=True)
    congress_gov_id = Column(String(50), unique=True, nullable=False)
    congress_id = Column(Integer, ForeignKey("congresses.id"))
    bill_type = Column(String(20), nullable=False)
    number = Column(Integer, nullable=False)
    display_number = Column(String(50))
    title = Column(Text)
    popular_title = Column(Text)
    short_title = Column(Text)
    official_title = Column(Text)
    sponsor_id = Column(Integer, ForeignKey("members.id"))
    origin_chamber = Column(String(20))
    status = Column(String(50))
    status_date = Column(Date)
    introduced_date = Column(Date)
    latest_action_date = Column(Date)
    latest_action = Column(Text)
    enacted_as = Column(String(50))
    law_number = Column(String(50))
    session_law = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def generate_universal_id(self):
        """Generate universal ID from congress, type, and number."""
        congress_number = getattr(self, "congress_number", None)
        if not congress_number and self.congress_id:
            # Look up congress number if needed
            from sqlalchemy.orm import Session
            from opendiscourse.database import sync_engine

            with Session(sync_engine) as session:
                congress = session.query(Congress).filter_by(id=self.congress_id).first()
                congress_number = congress.congress_number if congress else None

        self.universal_id = self._compute_universal_id(
            "bill", str(congress_number), self.bill_type.lower(), str(self.number)
        )

    sponsor = relationship("Member", back_populates="sponsored_bills", foreign_keys=[sponsor_id])
    actions = relationship("BillAction", back_populates="bill")
    cosponsors = relationship("BillCosponsor", back_populates="bill")
    summaries = relationship("BillSummary", back_populates="bill")
    texts = relationship("BillText", back_populates="bill")


class BillAction(Base):
    __tablename__ = "bill_actions"

    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    action_date = Column(DateTime, nullable=False)
    action_time = Column(DateTime)
    chamber = Column(String(20))
    action_type = Column(String(50))
    text = Column(Text)
    record_id = Column(String(50))
    source_system = Column(String(50))
    committee_id = Column(Integer, ForeignKey("committees.id"))
    created_at = Column(DateTime, server_default=func.now())

    bill = relationship("Bill", back_populates="actions")


class BillCosponsor(Base):
    __tablename__ = "bill_cosponsors"

    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    member_id = Column(Integer, ForeignKey("members.id"))
    is_original_cosponsor = Column(Boolean, default=False)
    sponsorship_date = Column(Date)
    withdrawal_date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())

    bill = relationship("Bill", back_populates="cosponsors")


class BillCommittee(Base):
    __tablename__ = "bill_committees"

    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    committee_id = Column(Integer, ForeignKey("committees.id"))
    activity = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())


class BillSubject(Base):
    __tablename__ = "bill_subjects"

    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    subject_type = Column(String(50))
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class BillSummary(Base):
    __tablename__ = "bill_summaries"

    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    action_date = Column(Date)
    action_description = Column(String(200))
    text = Column(Text, nullable=False)
    source = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())

    bill = relationship("Bill", back_populates="summaries")


class BillText(Base):
    __tablename__ = "bill_texts"

    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    version_code = Column(String(20))
    version_description = Column(String(200))
    url = Column(Text)
    format = Column(String(20))
    date = Column(Date)
    full_text = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    bill = relationship("Bill", back_populates="texts")


class RelatedBill(Base):
    __tablename__ = "related_bills"

    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    related_bill_id = Column(Integer, ForeignKey("bills.id"))
    relationship_type = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())


class Amendment(Base):
    __tablename__ = "amendments"

    id = Column(Integer, primary_key=True)
    congress_gov_id = Column(String(50), unique=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    amendment_type = Column(String(20))
    number = Column(Integer)
    description = Column(Text)
    purpose = Column(Text)
    sponsor_id = Column(Integer, ForeignKey("members.id"))
    proposed_date = Column(Date)
    status = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Vote(Base):
    __tablename__ = "votes"
    __table_args__ = (UniqueConstraint("congress_id", "chamber", "roll_number"),)

    id = Column(Integer, primary_key=True)
    congress_gov_id = Column(String(50), unique=True)
    congress_id = Column(Integer, ForeignKey("congresses.id"))
    chamber = Column(String(20), nullable=False)
    session = Column(String(10))
    roll_number = Column(Integer, nullable=False)
    vote_date = Column(Date, nullable=False)
    vote_time = Column(Time)
    question = Column(String(200))
    vote_type = Column(String(50))
    vote_result = Column(String(50))
    vote_description = Column(Text)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    amendment_id = Column(Integer, ForeignKey("amendments.id"))
    nomination_id = Column(Integer, ForeignKey("nominations.id"))
    majority_position = Column(String(20))
    total_yes = Column(Integer)
    total_no = Column(Integer)
    total_present = Column(Integer)
    total_not_voting = Column(Integer)
    required_majority = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())


class VotePosition(Base):
    __tablename__ = "vote_positions"

    id = Column(Integer, primary_key=True)
    vote_id = Column(Integer, ForeignKey("votes.id"))
    member_id = Column(Integer, ForeignKey("members.id"))
    position = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())


class Nomination(Base):
    __tablename__ = "nominations"

    id = Column(Integer, primary_key=True)
    congress_gov_id = Column(String(50), unique=True)
    congress_id = Column(Integer, ForeignKey("congresses.id"))
    number = Column(String(50))
    name = Column(String(200))
    position_title = Column(Text)
    organization = Column(Text)
    nominee_name = Column(String(200))
    nominee_state = Column(String(50))
    received_date = Column(Date)
    status = Column(String(50))
    committee_id = Column(Integer, ForeignKey("committees.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class NominationAction(Base):
    __tablename__ = "nomination_actions"

    id = Column(Integer, primary_key=True)
    nomination_id = Column(Integer, ForeignKey("nominations.id"))
    action_date = Column(Date)
    action = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class Treaty(Base):
    __tablename__ = "treaties"

    id = Column(Integer, primary_key=True)
    congress_gov_id = Column(String(50), unique=True)
    congress_id = Column(Integer, ForeignKey("congresses.id"))
    treaty_number = Column(Integer)
    resolution_number = Column(Integer)
    title = Column(Text)
    received_date = Column(Date)
    status = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class CommitteeReport(Base):
    __tablename__ = "committee_reports"

    id = Column(Integer, primary_key=True)
    congress_gov_id = Column(String(50), unique=True)
    congress_id = Column(Integer, ForeignKey("congresses.id"))
    report_type = Column(String(20))
    number = Column(Integer)
    title = Column(Text)
    committee_id = Column(Integer, ForeignKey("committees.id"))
    bill_id = Column(Integer, ForeignKey("bills.id"))
    date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class CongressionalRecord(Base):
    __tablename__ = "congressional_records"

    id = Column(Integer, primary_key=True)
    congress_gov_id = Column(String(50), unique=True)
    date = Column(Date, nullable=False)
    volume = Column(String(20))
    issue = Column(String(20))
    section = Column(String(20))
    url = Column(Text)
    pdf_url = Column(Text)
    full_text = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class FederalRegister(Base):
    __tablename__ = "federal_register"

    id = Column(Integer, primary_key=True)
    document_number = Column(String(50), unique=True)
    date = Column(Date, nullable=False)
    type = Column(String(50))
    title = Column(Text)
    agency = Column(String(200))
    docket_number = Column(String(100))
    pdf_url = Column(Text)
    html_url = Column(Text)
    full_text = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class CFREntry(Base):
    __tablename__ = "cfr_entries"

    id = Column(Integer, primary_key=True)
    title = Column(Integer, nullable=False)
    part = Column(Integer, nullable=False)
    section = Column(Integer)
    heading = Column(Text)
    text = Column(Text)
    last_updated = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
