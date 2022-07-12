<!-- Title - A concise title for the service that fits the pattern identified and in use across all services. -->
# Polaris Blood Glucose Readings API

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

<!-- Description - Fewer than 500 words that describe what a service delivers, providing an informative, descriptive, and comprehensive overview of the value a service brings to the table. -->
The BG Readings API is part of the Polaris platform (formerly DHOS). This service manages blood glucose readings, which 
contain information about a patient's health relating to diabetes, and details about these readings can be used by both
patients and clinicians to monitor their condition.

## Maintainers
The Polaris platform was created by Sensyne Health Ltd., and has now been made open-source. As a result, some of the
instructions, setup and configuration will no longer be relevant to third party contributors. For example, some of
the libraries used may not be publicly available, or docker images may not be accessible externally. In addition, 
CICD pipelines may no longer function.

For now, Sensyne Health Ltd. and its employees are the maintainers of this repository.

## Setup
These setup instructions assume you are using out-of-the-box installations of:
- `pre-commit` (https://pre-commit.com/)
- `pyenv` (https://github.com/pyenv/pyenv)
- `poetry` (https://python-poetry.org/)

You can run the following commands locally:
```bash
make install  # Creates a virtual environment using pyenv and installs the dependencies using poetry
make lint  # Runs linting/quality tools including black, isort and mypy
make test  # Runs unit tests
```

You can also run the service locally using the script `run_local.sh`, or in dockerized form by running:
```bash
docker build . -t <tag>
docker run <tag>
```

## Readings

Full details of the below are in the [API documentation](https://github.com/draysontechnologies/backend-api-specs/blob/master/swagger.yaml).

Readings have the following fields:

- Identifiers (the usual DHOS set of UUID, Created, Modified, URI)
- Timestamp (ISO8601 timestamp at which the Reading was measured)
- Value
- Unit (either "mmol/L" or "mg/dL")
- Comment (free text comment added by the patient)
- Doses (Object containing details of a given medication taken, details below)
- Prandial Tag (an enumerated object, details below)
- Banding (Object containing a classification of the reading, details below)
- Metadata (Object containing information about how the reading was taken, details below)

Readings are measured either in "mg/dL" (used mostly in the US and Germany) or in "mmol/L" (used internationally). Readings for healthy individuals are typically in the range 70-130 mg/dL, or 3.9-7.2 mmol/L.

Comments associated with Readings are added by patients and used (by both the patient and clinicians) to provide context for the Reading.

## Doses

After taking a pre-prandial (pre-meal) Reading, some patients will take medications to pre-emptively control their blood sugar glucose following the meal. For example, if a patient registers a particularly high pre-prandial reading they may choose to take more insulin than normal in order to bring their blood glucose levels back to the normal range.

Post-prandial Readings usually do not have doses associated with them.

A Dose consists of a medication and an amount. The Dose object has the following fields:

- Identifiers (the usual DHOS set of UUID, Created, Modified, URI)
- Medication UUID
- Amount

The Medication UUID contains the unique ID of a medication, the details of which can be retrieved using the [DHOS Medications API](https://github.com/draysontechnologies/dhos-medications-api/). These details also contain the unit of the Medication, which can be combined with the "amount" field of the Dose to understand the amount of the Medication that was taken.

## Prandial Tag

The Prandial Tag describes the circumstances in which the Reading was taken, most importantly whether it was pre-prandial (before a meal) or post-prandial (after a meal). The Prandial Tag must be one of a number of defined tags. Because of the interfaces between various systems within the Drayson Health products, the tags are defined by an integer value. In addition, the Prandial Tag types each have a human-readable UUID (for ease of debugging and testing).

The various Prandial Tags are enumerated here, along with their associated integer values:

- None (value 0)
- Before Breakfast (value 1)
- After Breakfast (value 2)
- Before Lunch (value 3)
- After Lunch (value 4)
- Before Dinner (value 5)
- After Dinner (value 6)
- Other (value 7)

**Note:** This list may change, grow or shrink, but **values associated with the different tags should never be changed** as this would cause the front-end clients to display Prandial Tags erroneously (unless there is a corresponding change in values for each client).

## Banding

When Readings are displayed in a patient diary or graph, the front-end needs to know whether to flag it as low, normal or high. This information is provided in the Banding, which is managed by the back-end (to prevent different interpretations of the same Reading).

The logic for calculating the Bandings can be found on [this page](https://wardenclyffe.draysontechnologies.com/display/PRODS/27.+Medication+and+Blood+Sugar+limits).

The various Bandings are enumerated here, along with their associated integer values:

- None (value 0)
- Low (value 1)
- Normal (value 2)
- High (value 3)

**Note:** This list may change, grow or shrink, but **values associated with the different bandings should never be changed** as this would cause the front-end clients to display Bandings erroneously (unless there is a corresponding change in values for each client).

## Metadata

Readings may be recorded manually, or via a Bluetooth/NFC connection from a meter. This information needs to be included with the Readings for support purposes. Certain other information is also included in the Metadata, for example whether a Reading was taken using control solution (for calibrating meters) instead of real blood.

The Metadata object has the following fields:

- Identifiers (the usual DHOS set of UUID, Created, Modified, URI)
- Manual (boolean - whether the reading was entered manually)
- Control (boolean - whether the reading was taken using control solution)
- Meter manufacturer
- Meter model
- Meter serial number

## Technical details

- CircleCI configuration for deployments
- Implementation code - primarily written to interact with [Flask](http://flask.pocoo.org/) and [SQLAlchemy](https://www.sqlalchemy.org/)
- Unit tests, to be run with the `tox` command, including:
  - PyTest tests
  - Code test coverage (fails below 90%) with [Coverage](https://coverage.readthedocs.io)
  - Static security analysis with [Bandit](https://wiki.openstack.org/wiki/Security/Projects/Bandit)
- Integration tests, to be run with MrTestRobot's `testrun` command (requires a running instance of this API against a real database)
- SQLAlchemy Alembic migrations to alter database structure and core state predictably
- Additional endpoints available when the environment variable ALLOW_DROP_DATA is set to true:
  - Data delete (found at /drop_data)
  
  ![alt text][viewer]

[viewer]: viewer_screenshot.png "Viewer screenshot"
