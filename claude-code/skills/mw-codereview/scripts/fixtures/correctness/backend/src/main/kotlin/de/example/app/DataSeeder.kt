package de.example.app

import org.springframework.boot.ApplicationArguments
import org.springframework.boot.ApplicationRunner
import org.springframework.context.annotation.Profile
import org.springframework.stereotype.Component
import org.springframework.stereotype.Service
import jakarta.annotation.PostConstruct

@Component
class DataSeeder(
    private val roleRepo: RoleRepository,
    private val settingRepo: SettingRepository,
    private val tagRepo: TagRepository,
) : ApplicationRunner {
  override fun run(args: ApplicationArguments) {
    seedRole("ADMIN")
    seedRole("USER")
    if (!roleRepo.existsByName("GUEST")) roleRepo.save(Role(name = "GUEST"))
    seedSetting("theme", "dark")
    upsertSetting("lang", "de")
    seedTags()
  }

  private fun seedTags() {
    val fresh = tagRepo.findByLabel("new")
    if (fresh == null) tagRepo.save(Tag(label = "new"))

    val existing = tagRepo.findByLabel("old")
    val target = existing ?: Tag(label = "old")
    target.label = "old"
    if (existing == null) tagRepo.save(target)
  }

  private fun seedRole(name: String) {
    roleRepo.findByName(name)
        ?: run {
          roleRepo.save(Role(name = name))
        }
  }

  private fun seedSetting(key: String, value: String) {
    val existing = settingRepo.findByKey(key)
    if (existing == null) settingRepo.save(Setting(key, value)) else existing.value = value
  }

  private fun upsertSetting(key: String, value: String) {
    settingRepo.findByKey(key)?.let { it.value = value } ?: settingRepo.save(Setting(key, value))
  }
}

@Component
@Profile("dev")
class DemoData(private val demoRepository: DemoRepository) {
  @PostConstruct
  fun fill() {
    if (demoRepository.count() == 0L) {
      demoRepository.saveAll(listOf(Demo(label = "one"), Demo(label = "two")))
    }
  }
}

@Service
class RoleService(private val roleRepo: RoleRepository) {
  fun getOrCreate(name: String): Role = roleRepo.findByName(name) ?: roleRepo.save(Role(name = name))
}
