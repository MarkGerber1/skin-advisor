import datetime
from sqlalchemy import (
	BigInteger,
	DateTime,
	ForeignKey,
	String,
	JSON,
	func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
	"""Базовая модель SQLAlchemy."""
	pass


class User(Base):
	__tablename__ = 'users'

	id: Mapped[int] = mapped_column(primary_key=True)
	user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
	username: Mapped[str] = mapped_column(String(32), nullable=True)
	first_name: Mapped[str] = mapped_column(String(64))
	created_at: Mapped[datetime.datetime] = mapped_column(
		DateTime, default=datetime.datetime.utcnow
	)

	survey_responses: Mapped[list["SurveyResponse"]] = relationship(back_populates="user")


class SurveyResponse(Base):
	__tablename__ = 'survey_responses'

	id: Mapped[int] = mapped_column(primary_key=True)
	user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id'))
	answers_json: Mapped[dict] = mapped_column(JSON)
	created_at: Mapped[datetime.datetime] = mapped_column(
		DateTime, default=datetime.datetime.utcnow, server_default=func.now()
	)

	user: Mapped["User"] = relationship(back_populates="survey_responses")
	diagnosis_result: Mapped["DiagnosisResult"] = relationship(back_populates="survey_response")


class DiagnosisResult(Base):
	__tablename__ = 'diagnosis_results'

	id: Mapped[int] = mapped_column(primary_key=True)
	survey_response_id: Mapped[int] = mapped_column(ForeignKey('survey_responses.id'))
	result_json: Mapped[dict] = mapped_column(JSON)
	created_at: Mapped[datetime.datetime] = mapped_column(
		DateTime, default=datetime.datetime.utcnow, server_default=func.now()
	)

	survey_response: Mapped["SurveyResponse"] = relationship(back_populates="diagnosis_result")


class SurveySession(Base):
	__tablename__ = 'survey_sessions'

	id: Mapped[int] = mapped_column(primary_key=True)
	user_id: Mapped[int] = mapped_column(BigInteger, index=True)
	status: Mapped[str] = mapped_column(String(32), default="started")
	answers_json: Mapped[dict] = mapped_column(JSON, default=dict)
	started_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
	updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
	finished_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)


class Recommendation(Base):
	__tablename__ = 'recommendations'

	id: Mapped[int] = mapped_column(primary_key=True)
	session_id: Mapped[int] = mapped_column(ForeignKey('survey_sessions.id'))
	summary_json: Mapped[dict] = mapped_column(JSON)
	products_json: Mapped[dict] = mapped_column(JSON)
	unavailable_json: Mapped[dict] = mapped_column(JSON)
	replaced_json: Mapped[dict] = mapped_column(JSON)
	created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class Download(Base):
	__tablename__ = 'downloads'

	id: Mapped[int] = mapped_column(primary_key=True)
	session_id: Mapped[int] = mapped_column(ForeignKey('survey_sessions.id'))
	pdf_path: Mapped[str] = mapped_column(String(512))
	created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

