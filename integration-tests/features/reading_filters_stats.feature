Feature: Get earliest, recent, and latest readings

  Background:
    Given RabbitMQ is running
    And the Trustomer API is running
    And readings for 7 days exist (4 ABNORMAL_READING messages are published to RabbitMQ)

  Scenario: Fetching earliest reading
    When the earliest reading is retrieved
    Then the reading API response status code is 200
      And the reading API response body is correct

  Scenario: Fetching latest reading
    When the latest reading is retrieved
    Then the reading API response status code is 200
      And the reading API response body is correct

  Scenario Outline: Fetching recent readings
    When the readings for the past <days> days are retrieved
    Then the expected readings were returned

    Examples:
       | days |
       | 7 |
       | 3 |

  Scenario Outline: Fetch statistics
    When statistics for the past <days> days are retrieved
    Then the statistics match <min>, <max>, <count>, <normal>

    Examples:
       | days | min | max | count | normal |
       | 7    |  2  | 14  |    7  |    3   |
       | 3    |  2  |  6  |    3  |    1   |
