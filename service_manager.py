#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CoinPulse Service Manager
코인펄스 서비스 관리 스크립트 (시작, 중지, 재시작, 상태확인)
"""

import os
import sys
import subprocess
import time
import signal
import psutil
import json
from pathlib import Path

# UTF-8 출력 설정 (Windows 호환)
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class CoinPulseServiceManager:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.pid_file = self.project_dir / "coinpulse.pid"
        self.log_file = self.project_dir / "coinpulse.log"
        
        # 서버 설정을 JSON 파일에서 로드
        self.servers = self.load_server_configs()
        
        self.processes = {}
    
    def load_server_configs(self):
        """JSON 설정 파일에서 서버 설정을 로드"""
        import json
        
        servers = {}
        
        # 차트 서버 설정 로드
        try:
            with open('chart_server_config.json', 'r', encoding='utf-8') as f:
                chart_config = json.load(f)
            chart_server_config = chart_config.get('server', {})
            servers["chart"] = {
                "script": "clean_upbit_server.py",
                "port": chart_server_config.get('port', 8080),
                "name": chart_server_config.get('name', 'Chart Server')
            }
        except FileNotFoundError:
            servers["chart"] = {
                "script": "clean_upbit_server.py",
                "port": 8080,
                "name": "Chart Server"
            }
        
        # 거래 서버 설정 로드
        try:
            with open('trading_server_config.json', 'r', encoding='utf-8') as f:
                trading_config = json.load(f)
            trading_server_config = trading_config.get('server', {})
            servers["trading"] = {
                "script": "simple_dual_server.py",
                "port": trading_server_config.get('port', 8081),
                "name": trading_server_config.get('name', 'Trading Server')
            }
        except FileNotFoundError:
            servers["trading"] = {
                "script": "simple_dual_server.py",
                "port": 8081,
                "name": "Trading Server"
            }
        
        return servers

    def log(self, message):
        """로그 메시지 출력 및 파일 저장"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")

    def is_port_in_use(self, port):
        """포트 사용 여부 확인"""
        # 먼저 소켓 기반 방법으로 확인 (더 안정적)
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                return result == 0
        except:
            pass
        
        # 소켓 방법이 실패하면 psutil 사용
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    return True
        except Exception:
            pass
        
        return False

    def find_process_by_port(self, port):
        """포트로 실행 중인 프로세스 찾기"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                for conn in proc.net_connections():
                    if conn.laddr.port == port and conn.status == 'LISTEN':
                        return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return None

    def kill_process_by_port(self, port):
        """포트로 실행 중인 프로세스 종료"""
        proc = self.find_process_by_port(port)
        if proc:
            try:
                self.log(f"포트 {port}에서 실행 중인 프로세스 종료: PID {proc.pid}")
                proc.terminate()
                
                # 프로세스가 종료될 때까지 대기
                for i in range(10):
                    if not proc.is_running():
                        break
                    time.sleep(0.5)
                else:
                    # 강제 종료
                    if proc.is_running():
                        self.log(f"프로세스 {proc.pid} 강제 종료 시도")
                        proc.kill()
                        time.sleep(1)
                
                return True
            except Exception as e:
                self.log(f"프로세스 종료 실패: {e}")
                return False
        return True

    def start_server(self, server_name):
        """개별 서버 시작"""
        if server_name not in self.servers:
            self.log(f"알 수 없는 서버: {server_name}")
            return False

        server_info = self.servers[server_name]
        script_path = self.project_dir / server_info["script"]
        port = server_info["port"]

        if not script_path.exists():
            self.log(f"스크립트 파일을 찾을 수 없습니다: {script_path}")
            return False

        # 포트가 이미 사용 중이면 종료
        if self.is_port_in_use(port):
            self.log(f"포트 {port}가 이미 사용 중입니다. 기존 프로세스를 종료합니다.")
            self.kill_process_by_port(port)
            # 포트가 완전히 해제될 때까지 대기
            for i in range(10):
                if not self.is_port_in_use(port):
                    break
                time.sleep(0.5)
            else:
                self.log(f"포트 {port} 해제 대기 시간 초과")

        try:
            self.log(f"{server_info['name']} 시작 중... (포트: {port})")
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.project_dir
            )
            
            # 프로세스가 정상적으로 시작되었는지 확인 (더 긴 대기 시간)
            time.sleep(5)
            
            # 프로세스가 여전히 실행 중인지 확인
            if process.poll() is None:
                # 포트가 실제로 열렸는지 확인
                if self.is_port_in_use(port):
                    self.processes[server_name] = process
                    self.log(f"{server_info['name']} 시작 완료 (PID: {process.pid})")
                    return True
                else:
                    self.log(f"{server_info['name']} 시작되었지만 포트 {port}가 열리지 않았습니다.")
                    process.terminate()
                    return False
            else:
                # 프로세스가 종료된 경우 오류 메시지 확인
                stdout, stderr = process.communicate()
                try:
                    error_msg = stderr.decode('utf-8', errors='ignore')
                except:
                    error_msg = str(stderr)
                self.log(f"{server_info['name']} 시작 실패: {error_msg}")
                return False
                
        except Exception as e:
            self.log(f"{server_info['name']} 시작 중 오류: {e}")
            return False

    def stop_server(self, server_name):
        """개별 서버 중지"""
        if server_name not in self.servers:
            self.log(f"알 수 없는 서버: {server_name}")
            return False

        server_info = self.servers[server_name]
        port = server_info["port"]

        # 메모리상의 프로세스 종료
        if server_name in self.processes:
            try:
                process = self.processes[server_name]
                if process.poll() is None:
                    self.log(f"{server_info['name']} 종료 중... (PID: {process.pid})")
                    process.terminate()
                    
                    # 프로세스가 종료될 때까지 대기
                    for i in range(10):
                        if process.poll() is not None:
                            break
                        time.sleep(0.5)
                    else:
                        # 강제 종료
                        if process.poll() is None:
                            self.log(f"프로세스 {process.pid} 강제 종료")
                            process.kill()
                            time.sleep(1)
                
                del self.processes[server_name]
            except Exception as e:
                self.log(f"프로세스 종료 중 오류: {e}")

        # 포트로 실행 중인 프로세스 종료
        if self.is_port_in_use(port):
            self.log(f"포트 {port}에서 실행 중인 {server_info['name']} 종료 중...")
            self.kill_process_by_port(port)

        self.log(f"{server_info['name']} 중지 완료")
        return True

    def start_all(self):
        """모든 서버 시작"""
        self.log("=" * 50)
        self.log("코인펄스 서비스 시작")
        self.log("=" * 50)

        # 설정 파일 생성
        try:
            from generate_config import generate_frontend_config
            generate_frontend_config()
            self.log("프론트엔드 설정 파일 생성 완료")
        except Exception as e:
            self.log(f"설정 파일 생성 실패: {e}")

        # Unicode 이모지 검사 (인코딩 오류 방지)
        if not self.check_unicode_safety():
            self.log("Unicode 이모지 검사 실패 - 서버 시작을 중단합니다.")
            return False
        
        success_count = 0
        for server_name in self.servers:
            if self.start_server(server_name):
                success_count += 1

        if success_count == len(self.servers):
            self.log("모든 서버가 성공적으로 시작되었습니다!")
            chart_port = self.servers["chart"]["port"]
            trading_port = self.servers["trading"]["port"]
            self.log(f"차트 서버: http://localhost:{chart_port}")
            self.log(f"거래 서버: http://localhost:{trading_port}")
            self.log(f"메인 앱: http://localhost:{chart_port}/frontend/trading_chart.html")
            return True
        else:
            self.log(f"일부 서버 시작 실패 ({success_count}/{len(self.servers)})")
            return False
    
    def check_unicode_safety(self):
        """Unicode 이모지 사용 여부 검사 (경고만 표시)"""
        try:
            import subprocess
            result = subprocess.run([sys.executable, "check_unicode.py"], 
                                 capture_output=True, text=True, cwd=self.project_dir,
                                 encoding='utf-8', errors='ignore')
            if result.returncode == 0:
                self.log("Unicode 이모지 검사 통과")
            else:
                self.log("[경고] Unicode 이모지가 발견되었습니다 (서비스는 정상 시작됩니다)")
                # 경고만 표시하고 서비스는 계속 시작
            return True
        except Exception as e:
            self.log(f"Unicode 검사 실행 실패: {e}")
            return True  # 검사 실패 시에도 서버는 시작

    def stop_all(self):
        """모든 서버 중지"""
        self.log("=" * 50)
        self.log("코인펄스 서비스 중지")
        self.log("=" * 50)

        for server_name in list(self.servers.keys()):
            self.stop_server(server_name)

        self.log("모든 서버가 중지되었습니다.")
        return True

    def restart_all(self):
        """모든 서버 재시작"""
        self.log("=" * 50)
        self.log("코인펄스 서비스 재시작")
        self.log("=" * 50)

        self.stop_all()
        time.sleep(2)
        return self.start_all()

    def status(self):
        """서버 상태 확인"""
        self.log("=" * 50)
        self.log("코인펄스 서비스 상태")
        self.log("=" * 50)

        for server_name, server_info in self.servers.items():
            port = server_info["port"]
            is_running = self.is_port_in_use(port)
            status_text = "실행 중" if is_running else "중지됨"
            
            self.log(f"{server_info['name']}: {status_text} (포트: {port})")
            
            if is_running:
                proc = self.find_process_by_port(port)
                if proc:
                    self.log(f"  PID: {proc.pid}")
                    self.log(f"  메모리 사용량: {proc.memory_info().rss / 1024 / 1024:.1f} MB")

    def show_menu(self):
        """메뉴 표시"""
        print("\n" + "=" * 50)
        print("CoinPulse Service Manager")
        print("=" * 50)
        print("1. Start Services")
        print("2. Stop Services") 
        print("3. Restart Services")
        print("4. Service Status")
        print("5. Exit")
        print("=" * 50)

def main():
    manager = CoinPulseServiceManager()
    
    if len(sys.argv) > 1:
        # 명령행 인수로 실행
        command = sys.argv[1].lower()
        
        if command == "start":
            manager.start_all()
        elif command == "stop":
            manager.stop_all()
        elif command == "restart":
            manager.restart_all()
        elif command == "status":
            manager.status()
        else:
            print("사용법: python service_manager.py [start|stop|restart|status]")
    else:
        # 대화형 메뉴
        while True:
            manager.show_menu()
            try:
                choice = input("선택하세요 (1-5): ").strip()
                
                if choice == "1":
                    manager.start_all()
                elif choice == "2":
                    manager.stop_all()
                elif choice == "3":
                    manager.restart_all()
                elif choice == "4":
                    manager.status()
                elif choice == "5":
                    print("Exiting...")
                    break
                else:
                    print("Invalid choice. Please select 1-5.")
                
                input("\nPress Enter to continue...")
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"오류 발생: {e}")

if __name__ == "__main__":
    main()
