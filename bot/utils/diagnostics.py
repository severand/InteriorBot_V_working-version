"""
🔍 DIAGNOSTICS SYSTEM - трекинг двойной отправки фото

Использование:
    from bot.utils.diagnostics import PhotoDiagnostics
    
    diag = PhotoDiagnostics()
    
    # Логируем answer_photo
    diag.log_answer_photo(user_id=123, msg_id=456, request_id="abc123")
    
    # Логируем edit_message_media
    diag.log_edit_message_media(user_id=123, msg_id=456, request_id="abc123")
    
    # Получим отчет
    report = diag.get_report(user_id=123)
    print(report)
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class PhotoDiagnostics:
    """
    🔍 Трекинг всех отправок фото
    """
    
    def __init__(self):
        # user_id -> request_id -> [(timestamp, method, msg_id, status)]
        self.photo_log: Dict[int, Dict[str, List]] = defaultdict(lambda: defaultdict(list))
        
    def log_photo_send(self, user_id: int, request_id: str, method: str, msg_id: int, status: str = "SUCCESS"):
        """
        Логируем отправку фото
        
        Methods: answer_photo, send_photo, edit_message_media, answer_photo_buffered
        Status: SUCCESS, FAILED, ATTEMPT_N
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'method': method,
            'msg_id': msg_id,
            'status': status,
        }
        
        self.photo_log[user_id][request_id].append(entry)
        
        # Необыкновенное логирование
        logger.warning(
            f"\ud83d\udcc8 [PHOTO_LOG] user_id={user_id}, request_id={request_id}, "
            f"method={method}, msg_id={msg_id}, status={status}"
        )
        
        # Обнаружение двойных отправок
        send_methods = [e['method'] for e in self.photo_log[user_id][request_id] 
                        if e['status'] == 'SUCCESS']
        
        if len(send_methods) > 1:
            logger.error(
                f"\ud83d\udd25 [DOUBLE_SEND_ALERT] user_id={user_id}, request_id={request_id}, "
                f"methods={send_methods}, all_log={self.photo_log[user_id][request_id]}"
            )
    
    def get_report(self, user_id: int) -> str:
        """
        Получить полный отчет по пользователю
        """
        if user_id not in self.photo_log:
            return f"No logs for user_id={user_id}"
        
        report = f"""

✨✨✨ PHOTO DIAGNOSTICS REPORT ✨✨✨
User ID: {user_id}
Total Requests: {len(self.photo_log[user_id])}

"""
        
        for request_id, entries in self.photo_log[user_id].items():
            success_count = len([e for e in entries if e['status'] == 'SUCCESS'])
            
            status_icon = "✅" if success_count == 1 else "\ud83d\udd25" if success_count > 1 else "\u274c"
            
            report += f"""
{status_icon} Request ID: {request_id}
   Total Sends: {len(entries)}
   Success Count: {success_count}
   Status: {'DOUBLE_SEND' if success_count > 1 else ('SUCCESS' if success_count == 1 else 'FAILED')}
   
   Timeline:
"""
            
            for i, entry in enumerate(entries, 1):
                report += f"     {i}. [{entry['timestamp']}] {entry['method']} -> msg_id={entry['msg_id']} ({entry['status']})\n"
        
        return report
    
    def get_json_report(self, user_id: int) -> dict:
        """
        Получить JSON отчет
        """
        return dict(self.photo_log.get(user_id, {}))
    
    def has_double_sends(self, user_id: int) -> bool:
        """
        Проверить, есть ли двойные отправки
        """
        if user_id not in self.photo_log:
            return False
        
        for request_id, entries in self.photo_log[user_id].items():
            success_count = len([e for e in entries if e['status'] == 'SUCCESS'])
            if success_count > 1:
                return True
        
        return False
    
    def get_double_sends(self) -> List[tuple]:
        """
        Получить все двойные отправки в системе
        
        Возвращает: [(user_id, request_id, methods, timestamp), ...]
        """
        doubles = []
        
        for user_id, requests in self.photo_log.items():
            for request_id, entries in requests.items():
                success_entries = [e for e in entries if e['status'] == 'SUCCESS']
                if len(success_entries) > 1:
                    methods = [e['method'] for e in success_entries]
                    timestamp = success_entries[0]['timestamp']
                    doubles.append((user_id, request_id, methods, timestamp))
        
        return doubles


# Глобальный экземпляр
diagnostics = PhotoDiagnostics()


def print_diagnostics_report():
    """
    Печать все диагностики в лог
    """
    doubles = diagnostics.get_double_sends()
    
    if not doubles:
        logger.info("\u2705 No double photo sends detected!")
        return
    
    logger.error(f"\ud83d\udd25 DOUBLE SENDS DETECTED: {len(doubles)} cases")
    
    for user_id, request_id, methods, timestamp in doubles:
        logger.error(
            f"\ud83d\udd25 CASE: user_id={user_id}, request_id={request_id}, "
            f"methods={methods}, timestamp={timestamp}"
        )
