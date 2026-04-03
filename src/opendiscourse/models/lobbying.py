from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from opendiscourse.database import Base


class OpenSecretsLegislator(Base):
    __tablename__ = "opensecrets_legislators"

    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    opensecrets_id = Column(String(20), unique=True)
    firstlast = Column(String(200))
    party = Column(String(50))
    office = Column(String(50))
    gender = Column(String(10))
    first_elected = Column(Integer)
    exit_code = Column(String(10))
    comments = Column(Text)
    phone = Column(String(30))
    fax = Column(String(30))
    website = Column(Text)
    webform = Column(Text)
    congress_office = Column(Text)
    bioguide_id = Column(String(20))
    votesmart_id = Column(Integer)
    fec_id = Column(String(20))
    govtrack_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class OpenSecretsCandidateSummary(Base):
    __tablename__ = "opensecrets_candidate_summaries"

    id = Column(Integer, primary_key=True)
    legislator_id = Column(Integer, ForeignKey("opensecrets_legislators.id"))
    cycle = Column(Integer, nullable=False)
    firstlast = Column(String(200))
    chamber = Column(String(20))
    party = Column(String(50))
    state = Column(String(50))
    total = Column(Numeric(14, 2))
    spent = Column(Numeric(14, 2))
    cash_on_hand = Column(Numeric(14, 2))
    debt = Column(Numeric(14, 2))
    origin = Column(String(50))
    source = Column(Text)
    last_updated = Column(Date)
    created_at = Column(DateTime, server_default=func.now())


class OpenSecretsContributor(Base):
    __tablename__ = "opensecrets_contributors"

    id = Column(Integer, primary_key=True)
    legislator_id = Column(Integer, ForeignKey("opensecrets_legislators.id"))
    cycle = Column(Integer, nullable=False)
    org_name = Column(String(300), nullable=False)
    total = Column(Numeric(14, 2), nullable=False)
    pacs = Column(Numeric(14, 2))
    indivs = Column(Numeric(14, 2))
    rank = Column(Integer)
    source = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class OpenSecretsIndustryContribution(Base):
    __tablename__ = "opensecrets_industry_contributions"

    id = Column(Integer, primary_key=True)
    legislator_id = Column(Integer, ForeignKey("opensecrets_legislators.id"))
    cycle = Column(Integer, nullable=False)
    industry_code = Column(String(10))
    industry_name = Column(String(200))
    total = Column(Numeric(14, 2))
    pacs = Column(Numeric(14, 2))
    indivs = Column(Numeric(14, 2))
    rank = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())


class OpenSecretsSectorContribution(Base):
    __tablename__ = "opensecrets_sector_contributions"

    id = Column(Integer, primary_key=True)
    legislator_id = Column(Integer, ForeignKey("opensecrets_legislators.id"))
    cycle = Column(Integer, nullable=False)
    sector_name = Column(String(100))
    sector_id = Column(String(10))
    total = Column(Numeric(14, 2))
    pacs = Column(Numeric(14, 2))
    indivs = Column(Numeric(14, 2))
    created_at = Column(DateTime, server_default=func.now())


class LobbyingDisclosure(Base):
    __tablename__ = "lobbying_disclosures"

    id = Column(Integer, primary_key=True)
    filing_id = Column(String(50), unique=True)
    registrant_name = Column(String(300))
    client_name = Column(String(300))
    lobby_year = Column(Integer)
    income = Column(Numeric(14, 2))
    expenses = Column(Numeric(14, 2))
    filing_date = Column(Date)
    filing_type = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())


class LobbyingIssue(Base):
    __tablename__ = "lobbying_issues"

    id = Column(Integer, primary_key=True)
    disclosure_id = Column(Integer, ForeignKey("lobbying_disclosures.id"))
    issue_code = Column(String(10))
    issue_description = Column(Text)
    specific_issues = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class LobbyingLobbyist(Base):
    __tablename__ = "lobbying_lobbyists"

    id = Column(Integer, primary_key=True)
    disclosure_id = Column(Integer, ForeignKey("lobbying_disclosures.id"))
    lobbyist_name = Column(String(200))
    covered_official_position = Column(String(200))
    created_at = Column(DateTime, server_default=func.now())


class LobbyingContact(Base):
    __tablename__ = "lobbying_contacts"

    id = Column(Integer, primary_key=True)
    disclosure_id = Column(Integer, ForeignKey("lobbying_disclosures.id"))
    senator_bioguide_id = Column(String(20))
    rep_bioguide_id = Column(String(20))
    house_member_id = Column(String(20))
    senate_member_id = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())
