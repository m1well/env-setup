package de.example.app

const val TEST_MAX = 1

class LimitsTest {
  fun tooLong() = "x".repeat(NOTE_MAX + TEST_MAX)
}
