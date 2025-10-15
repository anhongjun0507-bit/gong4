# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for
from collections import defaultdict
import logging

# 터미널 출력을 깔끔하게 하기 위해 로깅 설정
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# --- 기본 설정 ---
TOTAL_ARM BANDS = 13
TOTAL_FLAGS = 10
WORK_DESCRIPTION = "면회실 공사 작업"

# --- 데이터 저장소 (서버를 껐다 켜면 초기화) ---
on_site_records = []
total_entrants_today = 0
total_exits_today = 0


def _group_records():
    """현재 인원을 소속과 대표명 기준으로 그룹화하는 내부 함수"""
    if not on_site_records:
        return {}
    
    grouped = defaultdict(lambda: {'count': 0, 'vehicles': [], 'group_id': ''})
    
    for record in on_site_records:
        key = (record['소속'], record['대표명'])
        grouped[key]['count'] += 1
        if record['차량유무']:
            grouped[key]['vehicles'].append(record['차량'])
        grouped[key]['group_id'] = record['그룹ID'] # 그룹 ID는 동일하므로 덮어써도 무방
        
    return grouped


@app.route('/')
def index():
    """메인 페이지를 로드하고, 보고서 텍스트를 생성합니다."""
    
    # 보고서 생성 로직
    num_on_site = len(on_site_records)
    num_vehicles_on_site = sum(1 for rec in on_site_records if rec['차량유무'])
    armbands_issued = num_on_site
    flags_issued = num_vehicles_on_site
    armbands_held = TOTAL_ARM BANDS - armbands_issued
    flags_held = TOTAL_FLAGS - flags_issued

    report_parts = ["단결!", "공사 인원 입영 보고 드립니다.\n"]
    
    grouped_for_report = _group_records()
    for (affiliation, rep_name), data in grouped_for_report.items():
        count = data['count']
        personnel_str = f"{rep_name} 1명" if count == 1 else f"{rep_name} 등 {count}명"
        
        report_parts.append(f"소속: {affiliation}")
        report_parts.append(f"인원: {personnel_str}")
        if data['vehicles']:
            for vehicle in data['vehicles']:
                report_parts.append(f"차량: {vehicle}")
        report_parts.append("")

    report_parts.extend([
        "<완장 및 수기 보유 현황>",
        f"✅ 청색 완장: {armbands_held}개",
        f"✅ 청색 수기: {flags_held}개",
        "",
        f"불출 : 청색 완장 {armbands_issued}개, 수기 {flags_issued}개",
        "",
        f"오늘 공사내용은 {WORK_DESCRIPTION}입니다.",
        "",
        f"총 {total_entrants_today}명 입영 중 {total_exits_today}명 퇴영, {num_on_site}명 공사 중, 차량 {num_vehicles_on_site}대 입니다.",
        "",
        "이상입니다."
    ])
    entry_report_text = "\n".join(report_parts)
    
    # 템플릿에 전달할 데이터 준비 (딕셔너리를 리스트로 변환)
    records_list = [(key, data) for key, data in _group_records().items()]
    
    return render_template('index.html', records=records_list, report_text=entry_report_text)


@app.route('/add', methods=['POST']) # ⭐ 수정된 부분 1
def add_entry():
    """새로운 인원을 추가합니다."""
    global total_entrants_today
    
    affiliation = request.form['affiliation']
    rep_name = request.form['name']
    count = int(request.form['count'])
    vehicle = request.form['vehicle']
    has_vehicle = bool(vehicle.strip())
    
    # 고유한 그룹 ID 생성 (같은 그룹 퇴영 처리를 위함)
    group_id = f"{affiliation}_{rep_name}_{vehicle}"

    for i in range(count):
        on_site_records.append({
            "소속": affiliation,
            "대표명": rep_name,
            "차량": vehicle if i == 0 and has_vehicle else None,
            "차량유무": i == 0 and has_vehicle,
            "그룹ID": group_id
        })
    
    total_entrants_today += count
    return redirect(url_for('index'))


@app.route('/remove', methods=['POST']) # ⭐ 수정된 부분 2
def remove_entry():
    """선택한 그룹을 퇴영 처리합니다."""
    global total_exits_today, on_site_records
    
    group_id_to_remove = request.form['group_id']
    
    # 제거할 인원 수 계산
    removed_count = len([rec for rec in on_site_records if rec["그룹ID"] == group_id_to_remove])
    # 해당 그룹 ID를 가진 모든 기록 제거
    on_site_records = [rec for rec in on_site_records if rec["그룹ID"] != group_id_to_remove]
    
    total_exits_today += removed_count
    return redirect(url_for('index'))


@app.route('/clear', methods=['POST']) # ⭐ 수정된 부분 3
def clear_all():
    """모든 데이터를 초기화합니다."""
    global on_site_records, total_entrants_today, total_exits_today
    on_site_records.clear()
    total_entrants_today = 0
    total_exits_today = 0
    return redirect(url_for('index'))


if __name__ == '__main__':
    print("--- 🏗️ 공사 인원 관리 시스템 서버 시작 ---")
    print("1. 컴퓨터와 핸드폰을 같은 와이파이에 연결하세요.")
    print("2. 핸드폰 웹 브라우저를 열고 아래 주소로 접속하세요.")
    print(f"   (접속 주소 확인: 터미널에 'ipconfig' 또는 'ifconfig' 입력)")
    # host='0.0.0.0'으로 설정해야 외부(핸드폰)에서 접속 가능
    app.run(host='0.0.0.0', port=5000)
