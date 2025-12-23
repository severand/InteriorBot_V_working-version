import sqlite3

conn = sqlite3.connect('bot_data.db')
c = conn.cursor()

print('\n=== ПОСЛЕДНИЕ ГЕНЕРАЦИИ ===')
for row in c.execute('SELECT operation_type, success, created_at FROM generations WHERE user_id=7884972750 ORDER BY created_at DESC LIMIT 5'):
    print(f'{row[0]:15} | {"OK" if row[1] else "FAIL"} | {row[2]}')

print('\n=== ТЕКУЩЕЕ МЕНЮ ===')
for row in c.execute('SELECT menu_message_id, screen_code FROM chat_menus WHERE chat_id=7884972750'):
    print(f'Message ID: {row[0]} | Screen: {row[1]}')

print('\n=== БАЛАНС ===')
for row in c.execute('SELECT balance, total_generations FROM users WHERE user_id=7884972750'):
    print(f'Balance: {row[0]} | Total: {row[1]}')

conn.close()
