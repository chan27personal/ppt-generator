# 자가 호스팅 가이드 (완전 통제 · 무과금)

무료 VM에 **앱 + PostgreSQL(영구 저장) + 자동 HTTPS**를 Docker로 올립니다.
도메인도 **무료(DuckDNS)** 로 해결 → 누구나 `https://내주소.duckdns.org` 로 접속.

```
[사용자] ──https──▶ [Caddy(자동 HTTPS)] ──▶ [Streamlit 앱] ──▶ [PostgreSQL(영구)]
                         (무료 VM 1대, Docker 안에서 전부 실행)
```

## 0. 준비물 (모두 무료)
- 무료 서버 VM 1대 — **Oracle Cloud Always Free** 권장(평생 무료, ARM 24GB)
  - 대안: 집/사무실 상시 PC, GCP e2-micro 무료 등
- 무료 도메인 — **DuckDNS** (`*.duckdns.org`)

---
## 1. 무료 서버 만들기 (Oracle Cloud Always Free)
1. https://cloud.oracle.com 가입(무료) → 콘솔
2. **Compute → Instances → Create Instance**
   - Image: **Ubuntu 22.04**
   - Shape: **Ampere(ARM) Always Free** (또는 VM.Standard.E2.1.Micro)
   - SSH 키 등록(또는 생성해 다운로드)
3. 생성 후 **Public IP** 메모
4. **방화벽(보안목록) 열기**: VCN → Security List → Ingress 규칙에 **80, 443** (0.0.0.0/0) 추가

## 2. 도메인 연결 (DuckDNS, 무료)
1. https://www.duckdns.org → 구글/깃허브 로그인
2. 원하는 서브도메인 생성 (예 `myppt`) → `myppt.duckdns.org`
3. **current ip** 칸에 위 서버 Public IP 입력 → update

## 3. 서버 접속 & Docker 설치
```bash
ssh ubuntu@<서버IP>
# Docker 설치
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER && newgrp docker
# (Ubuntu 방화벽 쓰면) 포트 개방
sudo ufw allow 80 && sudo ufw allow 443 && sudo ufw allow OpenSSH && sudo ufw --force enable
# Oracle은 iptables도 막혀있을 수 있어 아래도 실행
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save || true
```

## 4. 앱 받아서 실행
```bash
git clone https://github.com/chan27personal/ppt-generator.git
cd ppt-generator
cp .env.example .env
nano .env            # POSTGRES_PASSWORD, DOMAIN(=myppt.duckdns.org) 수정
docker compose up -d --build
```
- 첫 빌드는 몇 분 걸립니다(LibreOffice 포함).
- 완료 후 **https://myppt.duckdns.org** 접속 → 끝! (Caddy가 인증서 자동 발급)

## 5. 운영
| 작업 | 명령 |
|---|---|
| 로그 보기 | `docker compose logs -f app` |
| 업데이트 | `git pull && docker compose up -d --build` |
| 재시작 | `docker compose restart` |
| 중지 | `docker compose down` (데이터는 볼륨에 유지) |
| **DB 백업** | `docker compose exec db pg_dump -U pptuser pptdb > backup_$(date +%F).sql` |
| DB 복원 | `cat backup.sql \| docker compose exec -T db psql -U pptuser pptdb` |

## 데이터 영구성
- PPT·메타데이터는 **PostgreSQL 볼륨(pgdata)** 에 저장 → 재시작/재배포해도 유지.
- 백업은 위 `pg_dump` 한 줄이면 전부(파일 포함, BLOB) 백업됩니다.

## 도메인 없이 IP로만 빠르게 테스트하려면
- `Caddyfile`의 `{$DOMAIN}` 을 `:80` 으로 바꾸고 `docker compose up -d` →
  `http://<서버IP>` 로 접속(HTTPS 아님, 테스트용).

## 트러블슈팅
- **접속 안 됨**: Oracle 보안목록 + ufw + iptables에서 80/443 열렸는지 확인.
- **인증서 실패**: DuckDNS IP가 서버 IP와 같은지, 80/443 외부 접근 가능한지 확인.
- **앱이 db 못 찾음**: `docker compose logs db` 로 DB 기동 확인(앱은 자동 재시도).
