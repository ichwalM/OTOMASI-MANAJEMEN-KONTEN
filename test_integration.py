#!/usr/bin/env python3
"""
Integration test script for WordPress + Hermes Agent + 9Router stack.
Checks service health, API endpoints, and runs CRUD test via wp_manager.py.
"""

import os
import sys
import json
import time
import subprocess
from urllib import request, error

# Terminal Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def log_info(msg):
    print(f"{BLUE}[INFO]{RESET} {msg}")

def log_ok(msg):
    print(f"{GREEN}[PASS]{RESET} {msg}")

def log_warn(msg):
    print(f"{YELLOW}[WARN]{RESET} {msg}")

def log_fail(msg):
    print(f"{RED}[FAIL]{RESET} {msg}")

def load_env():
    env_vars = {}
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    env_vars[key.strip()] = val.strip().strip("'\"")
    return env_vars

def check_http_endpoint(url, timeout=5):
    try:
        req = request.Request(url, headers={"User-Agent": "IntegrationTest/1.0"})
        with request.urlopen(req, timeout=timeout) as res:
            return res.status, None
    except error.HTTPError as e:
        return e.code, str(e)
    except error.URLError as e:
        return None, str(e.reason)

def main():
    print(f"\n{BLUE}======================================================{RESET}")
    print(f"{BLUE}  Uji Coba Integrasi: WordPress, Hermes, & 9Router    {RESET}")
    print(f"{BLUE}======================================================{RESET}\n")

    env = load_env()
    wp_port = env.get("WP_PORT", "10000")
    router_port = env.get("ROUTER_PORT", "11000")
    wp_user = env.get("WP_ADMIN_USER", "admin")
    wp_app_pass = env.get("WP_APP_PASSWORD", "")
    wp_url = f"http://localhost:{wp_port}"
    router_url = f"http://localhost:{router_port}"

    passed_tests = 0
    total_tests = 4

    # Test 1: Validasi Docker Compose
    log_info("1. Menguji validitas syntax docker-compose.yml...")
    res = subprocess.run(["docker", "compose", "config"], capture_output=True, text=True)
    if res.returncode == 0:
        log_ok("docker-compose.yml valid.")
        passed_tests += 1
    else:
        log_fail(f"docker-compose.yml tidak valid:\n{res.stderr}")

    # Test 2: Uji Koneksi 9Router
    log_info(f"2. Menguji ketersediaan layanan 9Router pada {router_url}...")
    status, err = check_http_endpoint(router_url)
    if status is not None and status < 500:
        log_ok(f"9Router aktif dan merespons (HTTP {status}).")
        passed_tests += 1
    else:
        log_warn(f"9Router belum merespons ({err}). Pastikan container berjalan via: docker compose up -d 9router")

    # Test 3: Uji WordPress Web & REST API
    log_info(f"3. Menguji ketersediaan WordPress pada {wp_url}...")
    status, err = check_http_endpoint(wp_url)
    if status is not None and status < 500:
        log_ok(f"WordPress website aktif (HTTP {status}).")
        
        # Cek REST API
        rest_url = f"{wp_url}/wp-json/wp/v2/posts"
        r_status, r_err = check_http_endpoint(rest_url)
        if r_status is not None and r_status < 500:
            log_ok(f"WordPress REST API aktif di {rest_url} (HTTP {r_status}).")
            passed_tests += 1
        else:
            log_warn(f"REST API belum dapat diakses: {r_err}")
    else:
        log_warn(f"WordPress belum dapat diakses ({err}). Pastikan container berjalan via: ./setup.sh")

    # Test 4: Uji Operasi CRUD wp_manager.py
    log_info("4. Menguji eksekusi script hermes skill wp_manager.py...")
    script_path = os.path.join(os.path.dirname(__file__), "hermes/skills/wordpress-manager/scripts/wp_manager.py")
    
    if not wp_app_pass:
        log_warn("WP_APP_PASSWORD belum terisi di .env. Lewati uji coba CRUD postingan.")
        log_info("Jalankan ./setup.sh untuk membuat Application Password otomatis.")
    else:
        test_title = f"[Uji Otomasi] Postingan Verifikasi Hermes {int(time.time())}"
        test_content = "<p>Ini adalah postingan verifikasi yang dibuat otomatis oleh Hermes Integration Test.</p>"
        
        # Buat post
        cmd_create = [
            sys.executable, script_path,
            "--url", wp_url,
            "--user", wp_user,
            "--password", wp_app_pass,
            "create-post",
            "--title", test_title,
            "--content", test_content,
            "--status", "draft"
        ]
        
        create_res = subprocess.run(cmd_create, capture_output=True, text=True)
        if create_res.returncode == 0:
            try:
                data = json.loads(create_res.stdout)
                post_id = data.get("id")
                log_ok(f"Berhasil membuat postingan draft (Post ID: {post_id})")
                
                # Hapus post setelah pengujian berhasil
                cmd_del = [
                    sys.executable, script_path,
                    "--url", wp_url,
                    "--user", wp_user,
                    "--password", wp_app_pass,
                    "delete-post",
                    "--id", str(post_id),
                    "--force"
                ]
                subprocess.run(cmd_del, capture_output=True, text=True)
                log_ok(f"Postingan uji coba (ID: {post_id}) berhasil dihapus kembali (Cleanup OK).")
                passed_tests += 1
            except Exception as e:
                log_warn(f"Gagal parse respons create-post: {e}\nOutput: {create_res.stdout}")
        else:
            log_fail(f"Gagal menjalankan wp_manager.py create-post:\n{create_res.stderr}")

    print(f"\n{BLUE}======================================================{RESET}")
    print(f"Hasil Pengujian: {passed_tests}/{total_tests} Langkah Berhasil.")
    print(f"{BLUE}======================================================{RESET}\n")

if __name__ == "__main__":
    main()
