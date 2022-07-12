Feature: Update a reading

  Background:
    Given RabbitMQ is running
    And the Trustomer API is running
    And a NORMAL BG reading exists

  Scenario Outline: Readings may be created and then modified
    When the BG reading is updated with <comment>, <dose>, <prandial_tag>
    Then the reading API response status code is 200
      And the reading API response body is correct
     And the fields have been updated

  Examples:
    | comment   | dose | prandial_tag     |
    | Ate early | 3    | BEFORE-BREAKFAST |
    | A comment |      |                  |
    |           | 5    | AFTER-DINNER     |
