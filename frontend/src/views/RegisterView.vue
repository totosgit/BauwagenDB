<template>
  <div class="login-page">
    <div class="login-card">
      <img src="/logo.png" class="login-logo" alt="" />
      <h1 class="login-title">Konto anlegen</h1>

      <!-- Erfolgsmeldung statt Formular -->
      <template v-if="done">
        <div class="done-box">
          <Icon name="warten" class="done-icon" />
          <p>{{ doneMessage }}</p>
        </div>
        <router-link to="/login" class="btn btn-primary btn-lg" style="width:100%; margin-top:8px">
          Zur Anmeldung
        </router-link>
      </template>

      <template v-else>
        <p class="login-subtitle">Ein Admin gibt dein Konto anschließend frei.</p>

        <form @submit.prevent="submit">
          <input
            v-model="form.display_name"
            type="text"
            placeholder="Dein Name (z.B. Tobias)"
            autocomplete="name"
            ref="inputEl"
            class="login-input"
            :disabled="loading"
          />
          <input
            v-model="form.username"
            type="text"
            placeholder="Benutzername zum Anmelden"
            autocomplete="username"
            autocapitalize="none"
            autocorrect="off"
            class="login-input"
            :disabled="loading"
          />
          <input
            v-model="form.password"
            type="password"
            placeholder="Passwort (mind. 8 Zeichen)"
            autocomplete="new-password"
            class="login-input"
            :disabled="loading"
          />
          <input
            v-model="form.password2"
            type="password"
            placeholder="Passwort wiederholen"
            autocomplete="new-password"
            class="login-input"
            :disabled="loading"
          />

          <div v-if="error" class="login-error">{{ error }}</div>

          <button type="submit" class="btn btn-primary btn-lg" style="width:100%; margin-top:16px" :disabled="loading">
            {{ loading ? '...' : 'Registrieren' }}
          </button>
        </form>

        <div class="login-foot">
          Schon ein Konto?
          <router-link to="/login">Anmelden</router-link>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { register } from '../api/index.js'
import Icon from '../components/Icon.vue'

const form = ref({ display_name: '', username: '', password: '', password2: '' })
const error = ref('')
const loading = ref(false)
const done = ref(false)
const doneMessage = ref('')
const inputEl = ref(null)

onMounted(() => inputEl.value?.focus())

function validate() {
  const f = form.value
  if (!f.display_name.trim()) return 'Bitte gib deinen Namen an'
  if (f.username.trim().length < 3) return 'Der Benutzername braucht mindestens 3 Zeichen'
  if (!/^[a-zA-Z0-9_.-]+$/.test(f.username.trim())) return 'Der Benutzername darf nur Buchstaben, Ziffern, Punkt, Minus und Unterstrich enthalten'
  if (f.password.length < 8) return 'Das Passwort braucht mindestens 8 Zeichen'
  if (f.password !== f.password2) return 'Die beiden Passwörter stimmen nicht überein'
  return ''
}

async function submit() {
  const problem = validate()
  if (problem) { error.value = problem; return }

  loading.value = true
  error.value = ''
  try {
    const res = await register({
      display_name: form.value.display_name.trim(),
      username: form.value.username.trim(),
      password: form.value.password,
    })
    doneMessage.value = res.detail || 'Konto angelegt. Ein Admin muss es noch freigeben.'
    done.value = true
  } catch (e) {
    const detail = e.response?.data?.detail
    error.value = typeof detail === 'string' ? detail : 'Registrierung fehlgeschlagen'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--cream);
  padding: 24px;
}
.login-card {
  background: var(--white);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 36px 28px 28px;
  width: 100%;
  max-width: 380px;
  text-align: center;
}
.login-logo {
  width: 84px; height: 84px;
  object-fit: contain;
  background: #ffffffcc;
  border-radius: 50%;
  padding: 4px;
  margin-bottom: 14px;
}
.login-title { font-size: 26px; font-weight: 800; margin-bottom: 6px; }
.login-subtitle { color: var(--text-muted); font-size: 15px; margin-bottom: 22px; line-height: 1.4; }
.login-input {
  width: 100%; padding: 14px 16px; margin-bottom: 10px;
  border: 1.5px solid var(--border); border-radius: var(--radius-sm);
  font-size: 17px; text-align: center;
  background: var(--surface-2); color: var(--text);
  -webkit-appearance: none;
}
.login-input:focus { outline: none; border-color: var(--green); }
.login-error {
  margin-top: 8px; color: var(--rot);
  font-size: 15px; font-weight: 600; line-height: 1.4;
}
.login-foot { margin-top: 22px; font-size: 15px; color: var(--text-muted); }
.login-foot a { color: var(--green-light); font-weight: 700; text-decoration: none; margin-left: 4px; }

.done-box {
  background: var(--surface-2);
  border-radius: var(--radius-sm);
  padding: 22px 18px;
  margin-bottom: 18px;
  line-height: 1.5;
  font-size: 16px;
}
.done-icon { font-size: 40px; margin-bottom: 10px; }
</style>
