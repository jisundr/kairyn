# depends: plugin/commands/init.md, plugin/scripts/*, plugin/stages/*, plugin/templates/*
Feature: kairyn init

  Scenario: Init creates a verified layout in a fresh repo
    Given fresh git repos
    When /kairyn:init runs once in each
    Then at least 90% of the repos pass verify-init

  Scenario: Init never overwrites an existing setup
    Given initialized repos with a user-edited learnings file
    When /kairyn:init runs once in each
    Then every .kairyn tree is unchanged
