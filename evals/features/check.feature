# depends: plugin/commands/check.md, plugin/scripts/*, plugin/harness/**/*
Feature: kairyn check

  Scenario: Check reports a harness doc with a broken header
    Given initialized repos where one workflow doc has lost its header
    When /kairyn:check runs once in each
    Then at least 90% of the replies name the broken doc
