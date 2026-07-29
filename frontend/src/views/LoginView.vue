<template>
  <div class="login-page">
    <div class="login-card">
      <img src="/logo.png" class="login-logo" alt="" />
      <h1 class="login-title">Blauwagen</h1>
      <p class="login-subtitle">Melde dich mit deinem Konto an</p>

      <form @submit.prevent="submit">
        <input
          v-model="username"
          type="text"
          placeholder="Benutzername"
          autocomplete="username"
          autocapitalize="none"
          autocorrect="off"
          ref="inputEl"
          class="login-input"
          :disabled="loading"
        />
        <input
          v-model="password"
          type="password"
          placeholder="Passwort"
          autocomplete="current-password"
          class="login-input"
          style="margin-top: 10px"
          :disabled="loading"
        />

        <div v-if="error" class="login-error">{{ error }}</div>

        <button type="submit" class="btn btn-primary btn-lg" style="width:100%; margin-top:16px" :disabled="loading">
          {{ loading ? '...' : 'Anmelden' }}
        </button>
      </form>

      <div class="login-foot">
        Noch kein Konto?
        <router-link to="/register">Registrieren</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { login } from '../api/index.js'
import { useAuth } from '../composables/useAuth.js'

const router = useRouter()
const route = useRoute()
const { refresh } = useAuth()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const inputEl = ref(null)

onMounted(() => inputEl.value?.focus())

async function submit() {
  if (!username.value.trim() || !password.value) return
  loading.value = true
  error.value = ''
  try {
    await login(username.value.trim(), password.value)
    await refresh()
    // Zurück dorthin, wo man eigentlich hinwollte
    router.replace(route.query.weiter || '/')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Anmeldung fehlgeschlagen'
    password.value = ''
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
.login-subtitle { color: var(--text-muted); font-size: 15px; margin-bottom: 24px; }
.login-input {
  width: 100%; padding: 14px 16px;
  border: 1.5px solid var(--border); border-radius: var(--radius-sm);
  font-size: 17px; text-align: center;
  background: var(--surface-2); color: var(--text);
  -webkit-appearance: none;
}
.login-input:focus { outline: none; border-color: var(--green); }
.login-error {
  margin-top: 14px; color: #f47070;
  font-size: 15px; font-weight: 600; line-height: 1.4;
}
.login-foot {
  margin-top: 22px; font-size: 15px; color: var(--text-muted);
}
.login-foot a { color: var(--green-light); font-weight: 700; text-decoration: none; margin-left: 4px; }
</style>
