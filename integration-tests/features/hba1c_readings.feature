Feature: Record Hba1c readings

  Background:
    Given the Trustomer API is running

  Scenario Outline: Hba1c reading is received for patient and recorded
    When a valid Hba1c reading of <value> <units> for patient <patient_uuid> is posted
    Then the Hba1c reading POST response is correct
      And the Hba1c reading is saved in the database
      And the patient summary can be retrieved without any BG readings
  Examples:
    | patient_uuid | value   | units    |
    | patient-1    | 40.5    | mmol/mol |
    | patient-1    | 41.0    | mmol/mol |

  Scenario Outline: Invalid Hba1c reading is received for patient
    When an invalid Hba1c reading of <value> <units> for patient <patient_uuid> is posted
      Then the Hba1c reading API response status is 400 if units are invalid
  Examples:
    | patient_uuid | value   | units    |
    | patient-1    | 40.5    | unknown  |

  Scenario: Hba1c reading update
      Given a new Hba1c reading is created
      When the Hba1c reading is updated
      Then the Hba1c reading is saved in the database

  Scenario: Hba1c reading delete
      Given a new Hba1c reading is created
      When the Hba1c reading is deleted
      Then the Hba1c reading can not be retrieved
