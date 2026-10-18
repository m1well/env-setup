package de.example.app

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.Id
import jakarta.persistence.Table
import jakarta.persistence.Version
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Modifying
import org.springframework.data.jpa.repository.Query
import java.util.UUID

@Entity
class Role(@Id val id: UUID = UUID.randomUUID(), var name: String)

@Entity
class Setting(@Id val key: String, var value: String)

@Entity
class Tag(@Id val id: UUID = UUID.randomUUID(), var label: String)

@Entity
class Demo(@Id val id: UUID = UUID.randomUUID(), var label: String)

@Entity
@Table(name = "event_slot")
class EventSlot(
    @Id val id: UUID,
    var title: String,
    var booked: Int,
    @Column(updatable = false) val taken: Int,
    @Version var version: Long,
)

@Entity
@Table(name = "page_counter")
class PageCounter(@Id val id: UUID, @Column(name = "hit_count") var hits: Long)

interface RoleRepository : JpaRepository<Role, UUID> {
  fun findByName(name: String): Role?
  fun existsByName(name: String): Boolean
}

interface SettingRepository : JpaRepository<Setting, String> {
  fun findByKey(key: String): Setting?
}

interface TagRepository : JpaRepository<Tag, UUID> {
  fun findByLabel(label: String): Tag?
}

interface DemoRepository : JpaRepository<Demo, UUID>

interface EventSlotRepository : JpaRepository<EventSlot, UUID> {
  @Modifying
  @Query("update event_slot set booked = booked + :n where id = :id", nativeQuery = true)
  fun book(id: UUID, n: Int): Int

  @Modifying
  @Query(
      """
      update event_slot set taken = taken + 1
      where id = :id
      """,
      nativeQuery = true,
  )
  fun take(id: UUID): Int

  @Modifying
  @Query("update event_slot set booked = booked - 1, version = version + 1 where id = :id", nativeQuery = true)
  fun cancelOne(id: UUID): Int

  @Modifying
  @Query("update EventSlot e set e.booked = e.booked - :n where e.id = :id")
  fun release(id: UUID, n: Int): Int
}

interface PageCounterRepository : JpaRepository<PageCounter, UUID> {
  @Modifying
  @Query("update page_counter set hit_count = hit_count + 1 where id = :id", nativeQuery = true)
  fun increment(id: UUID): Int
}
