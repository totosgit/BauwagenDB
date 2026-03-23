<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-icon">🚌</div>
      <h1 class="login-title">Bauwagen DB</h1>
      <p class="login-subtitle">Bitte Passwort eingeben</p>

      <form @submit.prevent="submit">
        <input
          v-model="password"
          type="password"
          placeholder="Passwort"
          autocomplete="current-password"
          ref="inputEl"
          class="login-input"
          :disabled="loading"
        />

        <div v-if="error" class="login-error">{{ error }}</div>

        <button type="submit" class="btn btn-primary btn-lg" style="width:100%; margin-top:12px" :disabled="loading">
          {{ loading ? '...' : 'Anmelden' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../api/index.js'

const router = useRouter()
const password = ref('')
const error = ref('')
const loading = ref(false)
const inputEl = ref(null)

onMounted(() => inputEl.value?.focus())

async function submit() {
  if (!password.value) return
  loading.value = true
  error.value = ''
  try {
    await login(password.value)
    router.replace('/')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Anmeldung fehlgeschlagen'
    password.value = ''
    inputEl.value?.focus()
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
  padding: 40px 28px;
  width: 100%;
  max-width: 380px;
  text-align: center;
}
.login-icon { font-size: 56px; margin-bottom: 12px; }
.login-title { font-size: 26px; font-weight: 700; margin-bottom: 6px; }
.login-subtitle { color: var(--text-muted); font-size: 15px; margin-bottom: 24px; }
.login-input {
  width: 100%; padding: 14px 16px;
  border: 1.5px solid var(--border); border-radius: var(--radius-sm);
  font-size: 18px; text-align: center; letter-spacing: 4px;
  -webkit-appearance: none;
}
.login-input:focus { outline: none; border-color: var(--green); }
.login-error {
  margin-top: 10px; color: #c62828;
  font-size: 15px; font-weight: 600;
}
</style>
