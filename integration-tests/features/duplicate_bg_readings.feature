Feature: Duplicate bg readings

  Background:
    Given the Trustomer API is running

  Scenario: Duplicate BG readings
    When a NORMAL BG reading is posted
    And the same BG reading is posted
    Then the reading API response status code is 409
      And the reading API response header contains Location

  Scenario: Duplicate BG readings v1
    When a NORMAL BG reading is posted using api v1
    And the same BG reading is posted using api v1
    Then the reading API response status code is 200
      And the reading API response body is correct
