import factory
from factory import fuzzy
from datetime import datetime
from ..ukrdc import PatientRecord

class PatientFactory(factory.alchemy.SQLAlchemyModelFactory):
    pid = Column(String, ForeignKey("patientrecord.pid"), primary_key=True)
    birth_time = Column("birthtime", Date)
    death_time = Column("deathtime", Date)
    gender = Column(String)
    country_of_birth = Column("countryofbirth", String)
    ethnic_group_code = Column("ethnicgroupcode", String)
    ethnic_group_description = Column("ethnicgroupdesc", String)
    person_to_contact_name = Column("persontocontactname", String)
    person_to_contact_number = Column("persontocontact_contactnumber", String)
    person_to_contact_relationship = Column("persontocontact_relationship", String)
    person_to_contact_number_comments = Column(
        "persontocontact_contactnumbercomments", String
    )
    person_to_contact_number_type = Column("persontocontact_contactnumbertype", String)
    occupation_code = Column("occupationcode", String)
    occupation_codestd = Column("occupationcodestd", String)
    occupation_description = Column("occupationdesc", String)
    primary_language = Column("primarylanguagecode", String)
    primary_language_codestd = Column("primarylanguagecodestd", String)
    primary_language_description = Column("primarylanguagedesc", String)
    dead = Column("death", Boolean)
    updated_on = Column("updatedon", DateTime)

    bloodgroup = Column(String)
    bloodrhesus = Column(String)

    dead = Column("death", Boolean)
    updated_on = Column("updatedon", DateTime)

class PatientRecordFactory(factory.alchemy.SQLAlchemyModelFactory):

    pid = factory.Sequence(lambda n: str(n).zfill(9))

    sendingfacility = factory.Faker("company")
    sendingextract = fuzzy.FuzzyChoice(["RADAR", "PV", "PKB"])
    localpatientid = fuzzy.FuzzyInteger(500_000_000, 599_999_999)
    ukrdcid = factory.Sequence(lambda n: str(n).zfill(9))

    extract_time = fuzzy.FuzzyNaiveDateTime(datetime(2018, 1, 1))
    creation_date = fuzzy.FuzzyNaiveDateTime(datetime(2018, 1, 1))
    update_date = fuzzy.FuzzyNaiveDateTime(datetime(2018, 1, 1))
    repository_creation_date = fuzzy.FuzzyNaiveDateTime(datetime(2018, 1, 1))
    repository_update_date = fuzzy.FuzzyNaiveDateTime(datetime(2018, 1, 1))

    class Meta:
        model = PatientRecord