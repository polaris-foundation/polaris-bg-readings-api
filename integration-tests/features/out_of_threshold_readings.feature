Feature: Out of threshold BG readings

  Background:
    Given RabbitMQ is running
    And the Trustomer API is running

  Scenario Outline: Out of threshold BG reading is received and published
    When a <banding> BG reading is posted
    Then the reading API response status code is 200
      And the reading API response body is correct
      And the reading is saved in the database
      And an ABNORMAL_READING message is published to RabbitMQ
  Examples:
    | banding |
    | HIGH    |
    | LOW     |
