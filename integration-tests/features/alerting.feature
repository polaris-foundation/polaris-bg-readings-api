Feature: Raising and clearing alerts

  Background:
    Given RabbitMQ is running
    And the Trustomer API is running
    And readings for 7 days exist (4 ABNORMAL_READING messages are published to RabbitMQ)

  Scenario Outline: Percentage Alert is generated and cleared
    When an <level> alert is generated
    Then a PATIENT_ALERT level PERCENTAGES_<level> message is published to RabbitMQ
     And the patient summary can be retrieved with <level> alert
    Then we clear the alert for the patient
     And the patient summary can be retrieved with no alert

    Examples:
    | level |
    | AMBER |
    | RED   |
