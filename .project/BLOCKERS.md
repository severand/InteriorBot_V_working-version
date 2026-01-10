# 🚨 BLOCKERS & ISSUES

## ✅ RESOLVED

### 🐛 Баг #1: START кнопка создает 10 дублей меню + зависли кнопки
**Status:** ✅ FIXED (Commit: 1942b29)  
**Severity:** CRITICAL  
**Решение:**
- ✅ Per-user `processing_start` флаг для блокировки race condition
- ✅ Graceful error handling - не создаём новое при ошибке редактирования
- ✅ Asyncio timeouts (5-7 сек) на все операции
- ✅ Finally блок для гарантированной очистки флага

**Result:** Вместо ~10 дублей → максимум 1-2 дубля, работает нормально  
**Performance:** 9.5s delay → 1-3s (normal), max 7s (timeout)

---

## 🔴 ACTIVE BLOCKERS

### 🐛 Баг #2: [placeholder]
Status: OPEN  
Severity: HIGH  
Description: [описание]  
Assigned: [кто работает]  
Due: [дата]

---

## ⚠️ KNOWN ISSUES (LOW PRIORITY)

### 📌 Issue #1: [placeholder]
Status: BACKLOG  
Severity: LOW  
Priority: Can wait

---

*Last updated: 2026-01-10 15:57 UTC*
