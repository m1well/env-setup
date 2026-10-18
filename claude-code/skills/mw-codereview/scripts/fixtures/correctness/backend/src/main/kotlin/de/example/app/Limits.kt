package de.example.app

import jakarta.validation.constraints.Size

const val TITLE_MAX = 100
const val NOTE_MAX = 500
private const val PAGE_LIMIT = 50

data class NoteRequest(@field:Size(max = TITLE_MAX) val title: String, val note: String)

class Pager {
  fun size(requested: Int): Int = minOf(requested, PAGE_LIMIT)

  companion object {
    const val MIN_AGE = 18
  }
}
