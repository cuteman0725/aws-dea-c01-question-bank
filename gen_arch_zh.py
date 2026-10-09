"""DEA-C01 架構圖版：一張 AWS 資料架構總圖，點題號亮起該題用到的服務與資料流向。

用法：
  python gen_arch_zh.py prep    # 從 answer_zh.json 切批次到 _work/arch_in_*.json
  python gen_arch_zh.py check _work/arch_out_001-038.json   # 檢查單一批次
  python gen_arch_zh.py build   # 合併 _work/arch_out_*.json，產生 arch_zh.json 與 Arch_ZH.html
"""
import glob
import html
import json
import os
import sys

from gen_short_zh import COMMUNITY, NOTE, load_notion

BASE = os.path.dirname(os.path.abspath(__file__))
ANSWER = os.path.join(BASE, "answer_zh.json")
WORK = os.path.join(BASE, "_work")
OUT_JSON = os.path.join(BASE, "arch_zh.json")
OUT_HTML = os.path.join(BASE, "Arch_ZH.html")

BATCH = 38
PATH_LEN = (2, 6)     # 每題資料流向的節點數
ALSO_MAX = 3          # 輔助節點（權限、加密、網路等）上限
BASE_EDGE_MIN = 3     # 至少幾題共用的連線才畫在底圖上

# 欄（由左到右）與橫帶；欄位寬 W_NODE、欄距 GAP
LANES = ["來源", "擷取・串流", "儲存", "目錄・治理・品質", "處理", "分析・資料庫", "使用端"]
W_NODE, H_NODE, GAP, ROW = 150, 56, 36, 72
X0, Y_MAIN, Y_TOP, Y_BOTTOM = 20, 176, 56, 648
WIDTH, HEIGHT = X0 * 2 + len(LANES) * W_NODE + (len(LANES) - 1) * GAP, 724

# id, 名稱, 副標, 位置（lane 欄號 / row 列號；band 為 top 或 bottom 時 lane 代表水平位置）, 說明
NODES = [
    ("src_db", "地端／外部 DB", "Oracle・SQL Server・MySQL", ("main", 0, 0), "來源資料庫：Oracle、SQL Server、MySQL、PostgreSQL、Teradata、SAP 等"),
    ("src_file", "地端檔案", "NAS・檔案伺服器・SFTP", ("main", 0, 1), "地端檔案系統、NAS、SFTP 用戶端、地端 Hadoop 檔案"),
    ("src_saas", "SaaS／第三方", "Salesforce・第三方資料", ("main", 0, 2), "Salesforce 等 SaaS 應用、第三方資料集"),
    ("src_stream", "串流來源", "IoT・點擊流・App 事件", ("main", 0, 3), "IoT 感測器、網站點擊流、App 與遊戲事件、應用程式日誌"),
    ("dms", "AWS DMS", "full load・CDC・SCT", ("main", 1, 0), "資料庫遷移與 CDC 持續複寫，搭配 SCT 轉換 schema"),
    ("datasync", "DataSync／傳輸", "Transfer Family・Gateway", ("main", 1, 1), "DataSync 排程同步檔案、Transfer Family（SFTP）、Storage Gateway"),
    ("appflow", "AppFlow", "SaaS 整合・Data Exchange", ("main", 1, 2), "AppFlow 免寫程式整合 SaaS；AWS Data Exchange 訂閱第三方資料"),
    ("kds", "Kinesis Data Streams", "KPL・KCL・shard", ("main", 1, 3), "即時串流：partition key、shard、KPL/KCL、enhanced fan-out"),
    ("msk", "Amazon MSK", "Kafka・Serverless", ("main", 1, 4), "託管 Kafka：MSK Serverless、Replicator、broker storage"),
    ("firehose", "Data Firehose", "投遞・格式轉換", ("main", 1, 5), "全託管投遞到 S3／Redshift／OpenSearch／Splunk，可轉 Parquet、呼叫 Lambda"),
    ("s3_tier", "S3 Lifecycle／保護", "IA・Glacier・Object Lock", ("main", 2, 0), "儲存類別（Standard-IA、Glacier、Intelligent-Tiering）、Lifecycle、Object Lock、Backup"),
    ("s3", "Amazon S3", "data lake・分區・事件", ("main", 2, 1, 2), "資料湖主儲存：分區、Parquet、事件通知、S3 Select、Object Lambda、versioning"),
    ("table_fmt", "Iceberg／Hudi", "MERGE・compaction", ("main", 2, 3), "開放表格式：MERGE／upsert、ACID、compaction、copy-on-write"),
    ("crawler", "Glue Crawler", "推斷 schema・加分區", ("main", 3, 0), "爬 S3／JDBC 推斷 schema、建表、更新分區"),
    ("catalog", "Glue Data Catalog", "metadata・分區索引", ("main", 3, 1), "中央 metadata：表、分區、partition index／projection、Schema Registry"),
    ("lf", "Lake Formation", "列欄權限・DataZone", ("main", 3, 2), "集中治理：列／欄級權限、data filter、LF-Tags、跨帳號共享、DataZone"),
    ("gdq", "Glue Data Quality", "DQDL・異常偵測", ("main", 3, 3), "DQDL 規則、ruleset、異常偵測、品質分數"),
    ("databrew", "Glue DataBrew", "recipe・profile", ("main", 3, 4), "視覺化 recipe 清理、profile job、PII 遮罩，幾乎不寫程式"),
    ("glue", "Glue ETL job", "Spark・bookmark・Flex", ("main", 4, 0), "serverless Spark／Python shell ETL：bookmark、Flex、DynamicFrame、FindMatches、Detect PII"),
    ("emr", "Amazon EMR", "Spark・Hive・Hadoop", ("main", 4, 1), "Spark／Hive／Hadoop 叢集、EMR step、runtime role"),
    ("lambda", "AWS Lambda", "事件驅動・layer", ("main", 4, 2), "事件驅動輕量運算：layer、concurrency、記憶體／CPU"),
    ("flink", "Managed Flink", "有狀態串流・視窗", ("main", 4, 3), "有狀態串流處理：時間視窗聚合、即時偵測"),
    ("athena", "Amazon Athena", "SQL 查 S3・workgroup", ("main", 5, 0), "serverless SQL 查 S3：分區裁剪、workgroup、federated query、結果重用"),
    ("redshift", "Amazon Redshift", "Serverless・Spectrum・MV", ("main", 5, 1), "資料倉儲：COPY／UNLOAD、Spectrum、data sharing、streaming ingestion、MV、分佈與排序鍵"),
    ("rds", "RDS／Aurora", "關聯式・zero-ETL", ("main", 5, 2), "關聯式資料庫：RDS、Aurora、zero-ETL 來源"),
    ("dynamodb", "DynamoDB", "毫秒讀寫・GSI・TTL", ("main", 5, 3), "NoSQL：GSI、TTL、Streams、DAX、容量模式"),
    ("opensearch", "OpenSearch", "搜尋・日誌分析", ("main", 5, 4), "搜尋與日誌分析、OpenSearch Dashboards"),
    ("neptune", "Neptune／Timestream", "圖形・時序資料庫", ("main", 5, 5), "圖形資料庫（Gremlin／SPARQL）與時序資料庫"),
    ("quicksight", "QuickSight", "儀表板・SPICE・Q", ("main", 6, 0), "BI 儀表板：SPICE、calculated field、LAC、Amazon Q"),
    ("users", "使用者／團隊", "分析師・部門・consumer", ("main", 6, 1), "分析師、部門、跨帳號 consumer 等存取者"),
    ("app", "應用程式／API", "Web App・API Gateway", ("main", 6, 2), "Web／行動 App、API Gateway、EKS／ECS 微服務、REST API"),
    ("ml", "SageMaker／AI", "Bedrock・Comprehend", ("main", 6, 3), "SageMaker、Bedrock、Comprehend、Redshift ML"),
    ("ec2", "EC2／EBS／EFS", "執行個體・區塊儲存", ("main", 6, 4), "EC2 執行個體、EBS volume、EFS 檔案系統"),
    ("eventbridge", "EventBridge", "事件規則・Scheduler", ("top", 2), "事件規則與排程：S3／Glue／Step Functions 事件觸發下一步"),
    ("glue_wf", "Glue Workflows", "trigger・crawler→job", ("top", 3), "Glue 原生編排：trigger 串 crawler 與 job"),
    ("sfn", "Step Functions", "Map・Choice・retry", ("top", 4), "serverless 狀態機：Map、Choice、Wait、callback、retry"),
    ("mwaa", "MWAA (Airflow)", "DAG・跨服務編排", ("top", 5), "託管 Apache Airflow：Python DAG 編排多服務"),
    ("sns_sqs", "SNS／SQS", "通知・佇列・DLQ", ("top", 6), "SNS 通知、SQS 佇列緩衝、DLQ"),
    ("vpc", "VPC／網路", "endpoint・SG・Direct Connect", ("bottom", 0), "subnet、security group、route table、VPC endpoint、Direct Connect、VPN"),
    ("secrets", "Secrets Manager", "憑證・自動輪換", ("bottom", 1), "集中保存資料庫憑證並自動輪換"),
    ("kms", "KMS／加密", "SSE-KMS・TLS", ("bottom", 2), "SSE-KMS、DSSE、金鑰權限、傳輸加密與憑證"),
    ("macie", "Macie", "S3 敏感資料探索", ("bottom", 3), "S3 敏感資料探索與分類，找出 PII"),
    ("iam", "IAM", "role・policy・RBAC", ("bottom", 4), "IAM role、policy、AssumeRole、IRSA、資料庫角色"),
    ("cloudtrail", "CloudTrail", "API・data events 稽核", ("bottom", 5), "記錄 API 與 S3 data events，做稽核"),
    ("cloudwatch", "CloudWatch", "Logs・metrics・alarm", ("bottom", 6), "Logs、metrics、alarm、subscription filter、Logs 資料保護政策"),
]
NODE_IDS = [n[0] for n in NODES]


def node_boxes():
    """回傳 {id: (x, y, w, h)}。"""
    boxes = {}
    for nid, _, _, pos, _ in NODES:
        x = X0 + pos[1] * (W_NODE + GAP)
        if pos[0] == "main":
            y = Y_MAIN + pos[2] * ROW
            rows = (pos[3] - pos[2] + 1) if len(pos) > 3 else 1
            h = H_NODE + (rows - 1) * ROW
        else:
            y = Y_TOP if pos[0] == "top" else Y_BOTTOM
            h = H_NODE
        boxes[nid] = (x, y, W_NODE, h)
    return boxes


def prep():
    os.makedirs(WORK, exist_ok=True)
    data = json.load(open(ANSWER, encoding="utf-8"))
    slim = [{"number": it["number"], "q": it["q"], "answer_text": it["answer_text"],
             "why": it["why"], "flow": it["flow"]} for it in data]
    for i in range(0, len(slim), BATCH):
        part = slim[i:i + BATCH]
        name = f"arch_in_{part[0]['number']:03d}-{part[-1]['number']:03d}.json"
        json.dump(part, open(os.path.join(WORK, name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(name, len(part))


def check(items, numbers):
    problems = []
    for n in numbers:
        it = items.get(n)
        if not it:
            problems.append(f"Q{n}: 缺少")
            continue
        path, also, key = it.get("path") or [], it.get("also") or [], it.get("key")
        bad = [x for x in path + also + [key] if x not in NODE_IDS]
        if bad:
            problems.append(f"Q{n}: 未知節點 {bad}")
        if not PATH_LEN[0] <= len(path) <= PATH_LEN[1]:
            problems.append(f"Q{n}: path {len(path)} 個節點")
        if any(a == b for a, b in zip(path, path[1:])):
            problems.append(f"Q{n}: path 有連續重複節點")
        if len(also) > ALSO_MAX or set(also) & set(path):
            problems.append(f"Q{n}: also 超過 {ALSO_MAX} 個或與 path 重複")
        if key not in path + also:
            problems.append(f"Q{n}: key 不在 path／also 中")
    return problems


def check_file(path):
    src = os.path.join(os.path.dirname(path), os.path.basename(path).replace("arch_out_", "arch_in_"))
    numbers = [it["number"] for it in json.load(open(src, encoding="utf-8"))]
    items = {it["number"]: it for it in json.load(open(path, encoding="utf-8"))}
    problems = check(items, numbers) + [f"Q{n}: 不屬於這一批" for n in items if n not in numbers]
    for p in problems:
        print(p)
    print(f"{os.path.basename(path)}：{len(items)}/{len(numbers)} 題，問題 {len(problems)} 筆")


def build():
    answers = json.load(open(ANSWER, encoding="utf-8"))
    meta, _, _ = load_notion()
    items = {}
    for f in sorted(glob.glob(os.path.join(WORK, "arch_out_*.json"))):
        for it in json.load(open(f, encoding="utf-8")):
            items[it["number"]] = it
    problems = check(items, [it["number"] for it in answers])
    for p in problems:
        print(p)
    print(f"共 {len(items)} 題，問題 {len(problems)} 筆")
    data = [{"number": n, "path": items[n]["path"], "key": items[n]["key"], "also": items[n].get("also", [])}
            for n in sorted(items)]
    open(OUT_JSON, "w", encoding="utf-8").write(
        "[\n" + ",\n".join(json.dumps(it, ensure_ascii=False) for it in data) + "\n]\n")
    open(OUT_HTML, "w", encoding="utf-8").write(render(answers, items, meta))
    print("已輸出", OUT_JSON, OUT_HTML)


CSS = """
*{box-sizing:border-box}
:root{--bg:#f4f5f7;--card:#fff;--fg:#1d1d1f;--sub:#666;--line:#d5d7dd;--ok:#1a7f37;--okbg:#e6f6ea;--ng:#c62828;--ngbg:#fdecea;
--acc:#ff9900;--accbg:#ffe8c2;--edge:#9aa0aa;
--l0:#eef0f3;--l1:#e5effb;--l2:#e4f4e8;--l3:#f1e9fa;--l4:#fdeee2;--l5:#e1f3f3;--l6:#fbe8ef;--lt:#fff6dc;--lb:#fdeaea}
@media(prefers-color-scheme:dark){:root{--bg:#111;--card:#1c1c1e;--fg:#eee;--sub:#9a9a9a;--line:#3a3a3e;--ok:#4cc26a;--okbg:#14301c;--ng:#ff6b6b;--ngbg:#3a1616;
--accbg:#4a3207;--edge:#6b707a;
--l0:#24262b;--l1:#1b2633;--l2:#1a2b20;--l3:#2a2233;--l4:#33261b;--l5:#183030;--l6:#33202a;--lt:#332c14;--lb:#341d1d}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 -apple-system,"Noto Sans TC","Microsoft JhengHei",sans-serif}
header{display:flex;gap:10px;align-items:center;padding:6px 10px;background:var(--card);border-bottom:1px solid var(--line)}
header b{font-size:15px;margin-right:auto}
header a{font-size:13px;color:var(--acc);white-space:nowrap}
#stage{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line)}
#map{height:44vh;overflow:auto;-webkit-overflow-scrolling:touch;position:relative;touch-action:pan-x pan-y}
#map svg{display:block}
#zoom{position:absolute;right:8px;top:8px;display:flex;gap:4px}
#zoom button,#bar button,#bar select{font-size:14px;padding:4px 9px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg)}
#bar{display:flex;gap:6px;align-items:center;padding:6px 8px;background:var(--card)}
#flt{flex:1;min-width:0}
#pos{font-size:13px;color:var(--sub);white-space:nowrap}
#side{padding:8px 6px 40px}
#info{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px;margin-bottom:10px}
#info .h{display:flex;gap:6px;align-items:center;flex-wrap:wrap;font-size:13px;color:var(--sub);margin-bottom:4px}
.tag{border-radius:4px;padding:0 6px;font-size:12px;background:var(--line);color:var(--fg)}
.tag.m{background:var(--acc);color:#000}
.tag.s{background:none;border:1px solid var(--line);color:var(--sub)}
.tag.w{background:var(--ngbg);color:var(--ng)}
#info .q{margin:0 0 6px}
#info .a{display:flex;gap:6px;padding:5px 6px;border-radius:6px;border:1px solid var(--ok);background:var(--okbg);color:var(--ok);margin-top:5px;font-weight:600}
#info .a i{font-style:normal;flex:none}
#info .y{margin:8px 0 0;font-size:15px}
#info .p{margin-top:8px;font-size:13px;display:flex;flex-wrap:wrap;gap:4px 2px;align-items:center}
#info .p span{border:1px solid var(--line);border-radius:6px;padding:1px 6px;background:var(--bg);white-space:nowrap}
#info .p span.k{border-color:var(--acc);background:var(--accbg);font-weight:600}
#info .p i{font-style:normal;color:var(--sub);margin:0 2px}
#info .n{margin-top:6px;font-size:13px;color:var(--sub)}
#info .lg{font-size:13px;color:var(--sub);margin:6px 0 0}
#chips{display:flex;gap:5px;overflow-x:auto;padding:6px 8px;background:var(--card);border-top:1px solid var(--line);scrollbar-width:thin}
#chips button{flex:none;min-width:44px;font-size:13px;padding:5px 4px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg)}
#chips button.d{border-style:dashed}
#chips button.cur{background:var(--acc);border-color:var(--acc);color:#000;font-weight:700}
.nd{cursor:pointer;transition:opacity .2s}
.nd rect{fill:var(--card);stroke:var(--line);stroke-width:1.2}
.nd text{fill:var(--fg);font-family:inherit}
.nd .lb{font-size:14px;font-weight:600}
.nd .sb{font-size:11px;fill:var(--sub)}
.lane{fill:var(--sub);font-size:13px;font-weight:600}
.band{stroke:none}
.be{fill:none;stroke:var(--edge);stroke-opacity:.45;transition:stroke-opacity .2s}
.mk-b{fill:var(--edge)}
.mk-a{fill:var(--acc)}
.he{fill:none;stroke:var(--acc);stroke-width:3;stroke-dasharray:8 5;animation:flow 1s linear infinite}
.ne{fill:none;stroke:var(--acc);stroke-opacity:.7}
@keyframes flow{to{stroke-dashoffset:-13}}
@media(prefers-reduced-motion:reduce){.he{animation:none;stroke-dasharray:none}}
svg.sel .nd{opacity:.2}
svg.sel .nd.on,svg.sel .nd.al{opacity:1}
svg.sel .be{stroke-opacity:.07}
.nd.on rect{stroke:var(--acc);stroke-width:2.5}
.nd.key rect{fill:var(--accbg);stroke-width:3.5}
.nd.al rect{stroke:var(--acc);stroke-dasharray:5 4;stroke-width:2}
.st rect{fill:var(--acc)}
.st text{fill:#000;font-size:12px;font-weight:700;text-anchor:middle}
@media(min-width:960px){
#layout{display:grid;grid-template-columns:minmax(0,1fr) 400px;align-items:start}
#stage{top:0;height:calc(100vh - 41px);display:flex;flex-direction:column;border-bottom:none;border-right:1px solid var(--line)}
#map{height:auto;flex:1}
#side{max-height:calc(100vh - 41px);overflow:auto;position:sticky;top:0}}
"""

JS = r"""
const LS='dea_arch_zh_',$=id=>document.getElementById(id),NS='http://www.w3.org/2000/svg';
const svg=$('svg'),map=$('map'),W=+svg.dataset.w,H=+svg.dataset.h,byN={};Q.forEach(q=>byN[q.n]=q);
const nodeEl={};svg.querySelectorAll('.nd').forEach(g=>nodeEl[g.dataset.id]=g);
const box=id=>N[id].slice(0,4),band=id=>N[id][7];
let scale=1,cur=null,set=[],focusNode=null;
function el(tag,attrs,parent){const e=document.createElementNS(NS,tag);for(const k in attrs)e.setAttribute(k,attrs[k]);if(parent)parent.appendChild(e);return e}
// 兩個節點之間的曲線：依相對位置選擇出發與抵達的邊
function route(a,b,off){
  const [ax,ay,aw,ah]=box(a),[bx,by,bw,bh]=box(b),acx=ax+aw/2,acy=ay+ah/2,bcx=bx+bw/2,bcy=by+bh/2,dx=bcx-acx,dy=bcy-acy;
  let p0,p3,n0,n3;
  const vert=(band(a)!=='main'||band(b)!=='main')?band(a)!==band(b):Math.abs(dx)<10;
  if(vert&&Math.abs(dx)<10&&band(a)===band(b)&&Math.abs(dy)>ROW+10){
    p0=[ax+aw,acy];p3=[bx+bw,bcy];n0=[1,0];n3=[1,0];
    const k=36+Math.abs(dy)/8;return curve(p0,p3,n0,n3,k,off)}
  if(vert){const d=dy>0?1:-1;p0=[acx,d>0?ay+ah:ay];p3=[bcx,d>0?by:by+bh];n0=[0,d];n3=[0,-d]}
  else{const d=dx>0?1:-1;p0=[d>0?ax+aw:ax,acy];p3=[d>0?bx:bx+bw,bcy];n0=[d,0];n3=[-d,0]}
  const dist=Math.hypot(p3[0]-p0[0],p3[1]-p0[1]);
  return curve(p0,p3,n0,n3,Math.min(140,Math.max(28,dist*.4)),off)}
function curve(p0,p3,n0,n3,k,off){
  const px=-(p3[1]-p0[1]),py=p3[0]-p0[0],l=Math.hypot(px,py)||1,ox=px/l*off,oy=py/l*off;
  const a=[p0[0]+ox,p0[1]+oy],b=[p3[0]+ox,p3[1]+oy];
  return `M${a[0]},${a[1]} C${a[0]+n0[0]*k},${a[1]+n0[1]*k} ${b[0]+n3[0]*k},${b[1]+n3[1]*k} ${b[0]},${b[1]}`}
const has=new Set(E.map(e=>e[0]+'>'+e[1]));
const gBase=$('base'),gHi=$('hi');
E.forEach(([a,b,f])=>el('path',{d:route(a,b,has.has(b+'>'+a)?5:0),class:'be','stroke-width':Math.min(4,.8+Math.log2(f)*.6),'marker-end':'url(#mb)'},gBase));
function setScale(s){scale=s;svg.style.width=W*s+'px';svg.style.height=H*s+'px'}
const fitS=()=>Math.min(map.clientWidth/W,map.clientHeight/H);
function focusIds(ids){
  if(!ids.length){setScale(fitS());map.scrollTo(0,0);return}
  let x1=1e9,y1=1e9,x2=0,y2=0;ids.forEach(id=>{const [x,y,w,h]=box(id);x1=Math.min(x1,x);y1=Math.min(y1,y);x2=Math.max(x2,x+w);y2=Math.max(y2,y+h)});
  const cw=map.clientWidth,ch=map.clientHeight,f=fitS();
  const s=Math.max(f,Math.min(cw/(x2-x1+40),ch/(y2-y1+40),1.1));
  setScale(s);map.scrollTo({left:(x1+x2)/2*s-cw/2,top:(y1+y2)/2*s-ch/2,behavior:'smooth'})}
function clearHi(){gHi.textContent='';Object.values(nodeEl).forEach(g=>g.classList.remove('on','key','al'))}
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function showQ(n,keepView){
  const q=byN[n];if(!q)return;cur=n;focusNode=null;localStorage.setItem(LS+'cur',n);
  clearHi();svg.classList.add('sel');
  const pairs=new Set(q.p.slice(1).map((id,i)=>q.p[i]+'>'+id));
  q.p.forEach((id,i)=>{nodeEl[id].classList.add('on');
    if(i)el('path',{d:route(q.p[i-1],id,pairs.has(id+'>'+q.p[i-1])?7:0),class:'he','marker-end':'url(#ma)'},gHi)});
  q.x.forEach(id=>nodeEl[id].classList.add('al'));nodeEl[q.k].classList.add('key');
  const steps={};q.p.forEach((id,i)=>(steps[id]=steps[id]||[]).push(i+1));
  Object.entries(steps).forEach(([id,nums])=>{const [x,y]=box(id),t=nums.join('・'),g=el('g',{class:'st'},gHi),r=t.length>1?17:11;
    el('rect',{x:x+4-r,y:y-7,width:r*2,height:22,rx:11},g);el('text',{x:x+4,y:y+8},g).textContent=t});
  const tags=(q.a.length>1?`<span class="tag m">複選 ${q.a.length}</span>`:'<span class="tag">單選</span>')+`<span class="tag s">${q.s}</span>`+(q.d?'<span class="tag w">⚠ 爭議</span>':'');
  const path=q.p.map(id=>`<span${id===q.k?' class="k"':''}>${esc(N[id][4])}</span>`).join('<i>→</i>');
  const also=q.x.length?`<div class="n">相關：${q.x.map(id=>esc(N[id][4])).join('、')}</div>`:'';
  $('info').innerHTML=`<div class="h"><b>Q${n}</b>${tags}</div><p class="q">${esc(q.q)}</p>`+
    q.t.map(([k,v])=>`<div class="a"><i>${k}</i><span>${esc(v)}</span></div>`).join('')+
    `<p class="y">${esc(q.w)}</p><div class="p">${path}</div>${also}`+(q.d?`<div class="n">${esc(q.d)}</div>`:'');
  document.querySelectorAll('#chips .cur').forEach(c=>c.classList.remove('cur'));
  const chip=$('c'+n);if(chip){chip.classList.add('cur');chips.scrollTo({left:chip.offsetLeft-chips.clientWidth/2+chip.offsetWidth/2,behavior:keepView?'auto':'smooth'})}
  $('side').scrollTop=0;
  updPos();focusIds(q.p.concat(q.x))}
function showNode(id){
  // 服務總覽：亮起這個服務，以及在相關題目中和它直接相連的服務
  cur=null;focusNode=id;localStorage.removeItem(LS+'cur');clearHi();svg.classList.add('sel');
  const cnt={},peers=new Set([id]);
  set.forEach(n=>{const p=byN[n].p;p.forEach((x,i)=>{if(i){const a=p[i-1];if(a===id||x===id){const k=a+'>'+x;cnt[k]=(cnt[k]||0)+1;peers.add(a);peers.add(x)}}})});
  Object.entries(cnt).forEach(([k,f])=>{const [a,b]=k.split('>');el('path',{d:route(a,b,cnt[b+'>'+a]?5:0),class:'ne','stroke-width':Math.min(5,1+Math.log2(f)),'marker-end':'url(#ma)'},gHi)});
  peers.forEach(x=>nodeEl[x].classList.add('on'));nodeEl[id].classList.add('key');
  const top=Object.entries(cnt).sort((a,b)=>b[1]-a[1]).slice(0,6).map(([k,f])=>{const [a,b]=k.split('>');return `${esc(N[a][4])} → ${esc(N[b][4])}（${f}）`});
  $('info').innerHTML=`<div class="h"><b>${esc(N[id][4])}</b><span class="tag s">${set.length} 題</span></div><p class="q">${esc(N[id][6])}</p>`+
    (top.length?`<div class="n">最常考的連線：<br>${top.join('<br>')}</div>`:'')+`<p class="lg">按 ▶ 從第一題開始，或點下方題號。</p>`;
  document.querySelectorAll('#chips .cur').forEach(c=>c.classList.remove('cur'));
  updPos();focusIds([...peers])}
function intro(){
  cur=null;focusNode=null;localStorage.removeItem(LS+'cur');clearHi();svg.classList.remove('sel');
  $('info').innerHTML=`<p class="q">342 題對應到同一張 AWS 資料架構圖。</p><p class="lg">點下方題號：亮起該題用到的服務，橘色箭頭與編號是資料流向，橘底是答案重點，虛線框是相關的權限、加密或網路設定。<br>點圖上的服務：看它和哪些服務最常一起考，下方只留相關題目。<br>底圖細線是 342 題中至少 ${BASE_MIN} 題出現的連線，越粗越常考。</p>`;
  updPos();focusIds([])}
function applyFlt(v,keep){
  localStorage.setItem(LS+'flt',v);$('flt').value=v;
  if(v==='all')set=Q.map(q=>q.n);
  else if(v==='dis')set=Q.filter(q=>q.d).map(q=>q.n);
  else if(v==='wrong'){let r={};try{r=JSON.parse(localStorage.getItem('dea_short_zh_res')||'{}')}catch(e){}set=Q.filter(q=>r[q.n]===0).map(q=>q.n)}
  else if(v[0]==='c'){const c=v.slice(1);set=Q.filter(q=>q.s.split('.')[0]===c).sort((a,b)=>a.o-b.o).map(q=>q.n)}
  else{const id=v.slice(2);set=Q.filter(q=>q.p.includes(id)||q.x.includes(id)).map(q=>q.n)}
  const inSet=new Set(set);
  document.querySelectorAll('#chips button').forEach(b=>b.style.display=inSet.has(+b.dataset.n)?'':'none');
  const node=v.startsWith('n:')?v.slice(2):null;
  if(node&&!keep)showNode(node);
  else if(cur&&inSet.has(cur))showQ(cur,true);
  else if(node)showNode(node);
  else intro()}
function updPos(){const i=set.indexOf(cur);$('pos').textContent=cur?`Q${cur}・${i+1}/${set.length}`:`${set.length} 題`}
function step(d){if(!set.length)return;let i=set.indexOf(cur);i=i<0?(d>0?0:set.length-1):(i+d+set.length)%set.length;showQ(set[i])}
// 題號按鈕（依章節順序）
const chips=$('chips');[...Q].sort((a,b)=>a.n-b.n).forEach(q=>{const b=document.createElement('button');b.id='c'+q.n;b.dataset.n=q.n;b.textContent=q.n;if(q.d)b.className='d';b.onclick=()=>showQ(q.n);chips.appendChild(b)});
Object.entries(nodeEl).forEach(([id,g])=>g.addEventListener('click',()=>applyFlt('n:'+id)));
$('prev').onclick=()=>step(-1);$('next').onclick=()=>step(1);
$('flt').onchange=e=>applyFlt(e.target.value);
$('zin').onclick=()=>{const c=[(map.scrollLeft+map.clientWidth/2)/scale,(map.scrollTop+map.clientHeight/2)/scale];setScale(Math.min(2,scale*1.3));map.scrollTo(c[0]*scale-map.clientWidth/2,c[1]*scale-map.clientHeight/2)};
$('zout').onclick=()=>{const c=[(map.scrollLeft+map.clientWidth/2)/scale,(map.scrollTop+map.clientHeight/2)/scale];setScale(Math.max(fitS(),scale/1.3));map.scrollTo(c[0]*scale-map.clientWidth/2,c[1]*scale-map.clientHeight/2)};
$('zfit').onclick=()=>{setScale(fitS());map.scrollTo(0,0)};
addEventListener('keydown',e=>{if(e.target.tagName==='SELECT')return;if(e.key==='ArrowRight')step(1);if(e.key==='ArrowLeft')step(-1)});
setScale(fitS());
const sf=localStorage.getItem(LS+'flt'),sc=+localStorage.getItem(LS+'cur');
if(sc&&byN[sc])cur=sc;
applyFlt(sf&&[...$('flt').options].some(o=>o.value===sf)?sf:'all',true);
"""


def svg_markup():
    boxes = node_boxes()
    lane_cls = {nid: (f"l{pos[1]}" if pos[0] == "main" else ("lt" if pos[0] == "top" else "lb"))
                for nid, _, _, pos, _ in NODES}
    out = [f'<svg id="svg" data-w="{WIDTH}" data-h="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" '
           f'aria-label="AWS 資料工程架構總圖：由左到右是來源、擷取、儲存、目錄治理、處理、分析與使用端，上方是編排，下方是安全與監控">',
           '<defs><marker id="mb" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
           '<path class="mk-b" d="M0,0L10,5L0,10z"/></marker>'
           '<marker id="ma" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" markerWidth="12" markerHeight="12" orient="auto-start-reverse">'
           '<path class="mk-a" d="M0,0L10,5L0,10z"/></marker></defs>']
    # 欄位與橫帶的底色
    for i, name in enumerate(LANES):
        x = X0 + i * (W_NODE + GAP)
        out.append(f'<rect class="band" x="{x - 8}" y="{Y_MAIN - 30}" width="{W_NODE + 16}" height="{6 * ROW + 2}" rx="10" style="fill:var(--l{i})"/>')
        out.append(f'<text class="lane" x="{x + W_NODE / 2}" y="{Y_MAIN - 12}" text-anchor="middle">{html.escape(name)}</text>')
    for y, label, var in ((Y_TOP, "編排・事件・通知", "--lt"), (Y_BOTTOM, "安全・監控・網路", "--lb")):
        out.append(f'<rect class="band" x="{X0 - 8}" y="{y - 30}" width="{WIDTH - 2 * X0 + 16}" height="{H_NODE + 38}" rx="10" style="fill:var({var})"/>')
        out.append(f'<text class="lane" x="{X0}" y="{y - 12}">{label}</text>')
    out.append('<g id="base"></g>')
    for nid, name, sub, pos, desc in NODES:
        x, y, w, h = boxes[nid]
        out.append(f'<g class="nd {lane_cls[nid]}" data-id="{nid}"><title>{html.escape(name)}：{html.escape(desc)}</title>'
                   f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>'
                   f'<text class="lb" x="{x + w / 2}" y="{y + h / 2 - 3}" text-anchor="middle">{html.escape(name)}</text>'
                   f'<text class="sb" x="{x + w / 2}" y="{y + h / 2 + 14}" text-anchor="middle">{html.escape(sub)}</text></g>')
    out.append('<g id="hi"></g></svg>')
    return "".join(out)


def render(answers, items, meta):
    from collections import Counter
    from gen_short_zh import sec_key
    chapters = meta["chapters"]
    disputed = set(meta["disputed"]) | set(COMMUNITY)
    dnote = {int(k): v for k, v in meta["disputed_note"].items()}
    order = sorted(answers, key=lambda it: (sec_key(it["section"]), it["number"]))
    rank = {it["number"]: i for i, it in enumerate(order)}
    q_data = []
    for it in answers:
        n = it["number"]
        x = items.get(n, {"path": [], "key": "", "also": []})
        note = ""
        if n in disputed:
            ds = [f"社群多選 {COMMUNITY[n]}"] if n in COMMUNITY else []
            if n in dnote and (n not in COMMUNITY or COMMUNITY[n] not in dnote[n]):
                ds.append(dnote[n])
            note = "⚠ " + ("；".join(ds) or "社群答案有分歧")
        if n in NOTE:
            note = (note + "　" if note else "") + "※ " + NOTE[n]
        q_data.append({"n": n, "q": it["q"], "a": it["answer"], "t": list(it["answer_text"].items()),
                       "s": it["section"], "o": rank[n], "w": it["why"], "p": x["path"], "k": x["key"],
                       "x": x.get("also", []), "d": note})
    boxes = node_boxes()
    pos_band = {nid: pos[0] for nid, _, _, pos, _ in NODES}
    n_data = {nid: [*boxes[nid], name, sub, desc, pos_band[nid]] for nid, name, sub, _, desc in NODES}
    freq = Counter((a, b) for it in items.values() for a, b in zip(it["path"], it["path"][1:]))
    e_data = [[a, b, f] for (a, b), f in sorted(freq.items(), key=lambda kv: -kv[1]) if f >= BASE_EDGE_MIN]
    use = Counter(x for it in items.values() for x in set(it["path"]) | set(it.get("also", [])))
    count = Counter(it["section"].split(".")[0] for it in answers)
    ch_opts = "".join(f'<option value="c{c}">{c}. {html.escape(v)}（{count.get(c, 0)}）</option>' for c, v in chapters.items())
    nd_opts = "".join(f'<option value="n:{nid}">{html.escape(name)}（{use[nid]}）</option>'
                      for nid, name, *_ in sorted(NODES, key=lambda n: -use[n[0]]) if use[nid])
    js_data = ("const Q=" + json.dumps(q_data, ensure_ascii=False, separators=(",", ":")) +
               ";const N=" + json.dumps(n_data, ensure_ascii=False, separators=(",", ":")) +
               ";const E=" + json.dumps(e_data, separators=(",", ":")) +
               f";const ROW={ROW},BASE_MIN={BASE_EDGE_MIN};")
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DEA-C01 架構圖</title><style>{CSS}</style></head><body>
<header><b>DEA-C01 架構圖 342 題</b><a href="Short_ZH.html">練習版</a><a href="Answer_ZH.html">速讀版</a></header>
<div id="layout"><div id="stage"><div id="map">{svg_markup()}</div>
<div id="zoom"><button id="zin" aria-label="放大">＋</button><button id="zout" aria-label="縮小">－</button><button id="zfit">全圖</button></div>
<div id="bar"><button id="prev" aria-label="上一題">◀</button>
<select id="flt"><option value="all">全部題目</option><option value="wrong">只看練習版錯題</option><option value="dis">只看爭議題</option>
<optgroup label="主題">{ch_opts}</optgroup><optgroup label="服務">{nd_opts}</optgroup></select>
<span id="pos"></span><button id="next" aria-label="下一題">▶</button></div><div id="chips"></div></div>
<div id="side"><article id="info"></article></div></div>
<script>{js_data}{JS}</script></body></html>"""


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "check":
        check_file(sys.argv[2])
    else:
        {"prep": prep, "build": build}[cmd]()
