from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from opendiscourse.database import Base


class StockDisclosure(Base):
    __tablename__ = "stock_disclosures"

    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    filing_date = Column(Date, nullable=False)
    report_type = Column(String(50))
    report_url = Column(Text)
    pdf_url = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class StockTransaction(Base):
    __tablename__ = "stock_transactions"

    id = Column(Integer, primary_key=True)
    disclosure_id = Column(Integer, ForeignKey("stock_disclosures.id"))
    member_id = Column(Integer, ForeignKey("members.id"))
    filer_name = Column(String(200))
    filer_relation = Column(String(50))
    asset_name = Column(String(300), nullable=False)
    asset_type = Column(String(50))
    ticker = Column(String(20))
    cusip = Column(String(20))
    transaction_type = Column(String(50))
    transaction_date = Column(Date)
    transaction_amount_low = Column(Numeric(12, 2))
    transaction_amount_high = Column(Numeric(12, 2))
    transaction_amount = Column(Numeric(14, 2))
    ownership_type = Column(String(50))
    comment = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class FinancialDisclosure(Base):
    __tablename__ = "financial_disclosures"

    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    year = Column(Integer, nullable=False)
    filing_type = Column(String(50))
    pdf_url = Column(Text)
    filing_date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())


class FinancialPosition(Base):
    __tablename__ = "financial_positions"

    id = Column(Integer, primary_key=True)
    disclosure_id = Column(Integer, ForeignKey("financial_disclosures.id"))
    organization_name = Column(String(300))
    position_title = Column(String(200))
    created_at = Column(DateTime, server_default=func.now())


class FinancialAgreement(Base):
    __tablename__ = "financial_agreements"

    id = Column(Integer, primary_key=True)
    disclosure_id = Column(Integer, ForeignKey("financial_disclosures.id"))
    party_name = Column(String(300))
    terms_or_date = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class FinancialGift(Base):
    __tablename__ = "financial_gifts"

    id = Column(Integer, primary_key=True)
    disclosure_id = Column(Integer, ForeignKey("financial_disclosures.id"))
    source_name = Column(String(300))
    description = Column(Text)
    value = Column(Numeric(12, 2))
    created_at = Column(DateTime, server_default=func.now())


class FinancialTravel(Base):
    __tablename__ = "financial_travel"

    id = Column(Integer, primary_key=True)
    disclosure_id = Column(Integer, ForeignKey("financial_disclosures.id"))
    source_name = Column(String(300))
    destination = Column(String(200))
    dates = Column(String(100))
    purpose = Column(String(200))
    amount = Column(Numeric(12, 2))
    created_at = Column(DateTime, server_default=func.now())


class FinancialAsset(Base):
    __tablename__ = "financial_assets"

    id = Column(Integer, primary_key=True)
    disclosure_id = Column(Integer, ForeignKey("financial_disclosures.id"))
    asset_name = Column(String(300))
    asset_type = Column(String(100))
    value_low = Column(Numeric(14, 2))
    value_high = Column(Numeric(14, 2))
    income_type = Column(String(50))
    income_low = Column(Numeric(14, 2))
    income_high = Column(Numeric(14, 2))
    created_at = Column(DateTime, server_default=func.now())
