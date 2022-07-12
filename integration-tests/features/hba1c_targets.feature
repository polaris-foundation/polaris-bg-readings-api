Feature: Record Hba1c targets

  Scenario: Hba1c target creation
      Given the Trustomer API is running
      And a new Hba1c target is created
      When the Hba1c target is updated
      Then the Hba1c targets can be retrieved
