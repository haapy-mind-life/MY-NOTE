import streamlit as st
import os
import json
import subprocess
import webbrowser
from datetime import datetime
import yaml

################################
# 0. 전역 설정(상수)
################################
DOCS_DIR = "docs"
METADATA_FILE = "metadata.json"
TEMPLATES_FILE = "templates.json"
PROMPTS_FILE = "prompts.json"
KEYWORDS_FILE = "keywords.json"
MKDOCS_CONFIG = "mkdocs.yml"

################################
# 1. JSON 로드/저장 함수
################################
def load_json(file_path: str) -> dict:
    """JSON 파일 로드."""
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_json(file_path: str, data: dict):
    """JSON 데이터를 파일로 저장."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

################################
# 2. MkDocs 설정 및 필수 파일 확인
################################
def mkdocs_setup():
    """MkDocs 설정 파일 및 필수 파일 확인 및 생성."""
    metadata = load_json(METADATA_FILE)
    templates = load_json(TEMPLATES_FILE)
    prompts = load_json(PROMPTS_FILE)
    keywords = load_json(KEYWORDS_FILE)

    # MkDocs 설정 파일 생성
    mkdocs_config = {
        "site_name": "MY-NOTE",
        "theme": {"name": "material"},
        "nav": [{"Home": "index.md"}],
        "docs_dir": DOCS_DIR,
        "plugins": ["search"],
        "markdown_extensions": [
            "admonition",
            "codehilite",
            {"toc": {"permalink": True}},
            "footnotes",
            "meta"
        ]
    }

    # 문서 추가
    for fname, meta in metadata.items():
        nav_entry = {meta["title"]: fname}
        mkdocs_config["nav"].append(nav_entry)

    # 템플릿, 프롬프트, 키워드 추가
    if templates:
        mkdocs_config["nav"].append({"Templates": "templates.md"})
    if prompts:
        mkdocs_config["nav"].append({"Prompts": "prompts.md"})
    if keywords:
        mkdocs_config["nav"].append({"Keywords": "keywords.md"})

    # 설정 파일 저장
    with open(MKDOCS_CONFIG, "w", encoding="utf-8") as f:
        yaml.dump(mkdocs_config, f, allow_unicode=True)

    # 필수 파일 확인 및 생성
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)
    index_file_path = os.path.join(DOCS_DIR, "index.md")
    if not os.path.exists(index_file_path):
        with open(index_file_path, "w", encoding="utf-8") as f:
            f.write("# Welcome to MY-NOTE\n\nThis is your project's index page.")

################################
# 3. 문서 CRUD
################################
def generate_filename() -> str:
    """'YYYY-MM-DD-#n.md' 형태로 파일명을 생성."""
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)
    date_str = datetime.now().strftime("%Y-%m-%d")
    counter = 1
    while True:
        filename = f"{date_str}-#{counter}.md"
        if not os.path.exists(os.path.join(DOCS_DIR, filename)):
            return filename
        counter += 1

def create_document(title: str, category: str, tags: list, content: str) -> str:
    """새 문서를 생성하고 metadata.json에 등록."""
    metadata = load_json(METADATA_FILE)
    file_name = generate_filename()

    front_matter = [
        "---",
        f'title: "{title}"',
        f'category: "{category}"',
        f'tags: {tags}',
        "---\n"
    ]
    file_path = os.path.join(DOCS_DIR, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(front_matter))
        f.write(content)

    metadata[file_name] = {
        "title": title,
        "category": category,
        "tags": tags
    }
    save_json(METADATA_FILE, metadata)

    return file_name

def load_markdown_file(file_name: str) -> str:
    """Markdown 파일 로드."""
    file_path = os.path.join(DOCS_DIR, file_name)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def delete_document(file_name: str):
    """문서를 삭제하고 metadata.json에서 제거."""
    metadata = load_json(METADATA_FILE)
    if file_name in metadata:
        del metadata[file_name]
        save_json(METADATA_FILE, metadata)
    file_path = os.path.join(DOCS_DIR, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)

################################
# 4. MkDocs 관리 함수
################################
def mkdocs_build():
    """MkDocs 빌드."""
    mkdocs_setup()
    try:
        subprocess.run(["mkdocs", "build"], check=True)
        return "MkDocs 빌드 완료!"
    except subprocess.CalledProcessError as e:
        return f"빌드 오류 발생: {e}"

def mkdocs_serve():
    """MkDocs 로컬 테스트."""
    mkdocs_setup()
    try:
        subprocess.Popen(["mkdocs", "serve"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        webbrowser.open("http://127.0.0.1:8000")
        return "MkDocs 로컬 테스트 서버가 시작되었습니다."
    except Exception as e:
        return f"로컬 테스트 오류 발생: {e}"

def mkdocs_deploy():
    """MkDocs 배포."""
    mkdocs_setup()
    try:
        subprocess.run(["mkdocs", "gh-deploy"], check=True)
        return "MkDocs 배포 완료! GitHub Pages에서 확인하세요."
    except subprocess.CalledProcessError as e:
        return f"배포 오류 발생: {e}"

################################
# 6. Markdown 파일 병합 함수
################################
def merge_md_files(folder_path: str, output_file: str):
    """
    특정 폴더 내 모든 .md 파일을 합쳐 하나의 파일로 저장합니다.
    """
    if not os.path.exists(folder_path):
        return f"지정된 폴더가 존재하지 않습니다: {folder_path}"

    try:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            outfile.write(f"# MERGED Overview ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n\n")
            outfile.write(f"합쳐진 폴더: {folder_path}\n\n")
            
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            outfile.write(f"## {file}\n\n")
                            outfile.write(infile.read() + '\n\n')
                            outfile.write('-' * 40 + '\n\n')
        return f"Merged 파일이 성공적으로 생성되었습니다: {output_file}"
    except Exception as e:
        return f"파일 병합 중 오류 발생: {e}"


################################
# 5. Streamlit 메인
################################
def main():
    st.title("MY-NOTE")
    st.sidebar.title("메뉴")
    menu = st.sidebar.radio("선택", [
        "문서 관리", 
        "템플릿 관리", 
        "프롬프트 관리", 
        "키워드 관리", 
        "MkDocs 관리", 
        "MERGED 파일 생성"  # 추가된 메뉴
    ])

    ################################
    # 문서 관리
    ################################
    if menu == "문서 관리":
        st.header("문서 관리")
        action = st.selectbox("작업 선택", ["보기", "추가", "수정", "삭제"])

        metadata = load_json(METADATA_FILE)
        if action == "보기":
            st.subheader("문서 보기")
            if metadata:
                for fname, doc_meta in metadata.items():
                    with st.expander(f"{doc_meta['title']} ({fname})"):
                        st.write(f"**카테고리:** {doc_meta['category']}")
                        st.write(f"**태그:** {', '.join(doc_meta['tags'])}")
                        content = load_markdown_file(fname)
                        st.text_area("문서 내용", value=content, height=200, disabled=True)
            else:
                st.info("등록된 문서가 없습니다.")

        elif action == "추가":
            st.subheader("문서 추가")
            title = st.text_input("문서 제목")
            category = st.text_input("카테고리")
            tags_input = st.text_input("태그 (쉼표로 구분)")
            tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]
            content = st.text_area("본문 내용", height=200)

            if st.button("문서 추가"):
                if not title:
                    st.error("제목을 입력하세요.")
                else:
                    file_name = create_document(title, category, tags, content)
                    st.success(f"문서 '{file_name}'이 추가되었습니다.")

        elif action == "수정":
            st.subheader("문서 수정")
            if metadata:
                file_name = st.selectbox("수정할 문서 선택", list(metadata.keys()))
                doc_meta = metadata[file_name]
                title = st.text_input("제목", value=doc_meta["title"])
                category = st.text_input("카테고리", value=doc_meta["category"])
                tags = st.text_input("태그", value=", ".join(doc_meta["tags"]))
                content = st.text_area("본문 내용", value=load_markdown_file(file_name), height=200)

                if st.button("수정 완료"):
                    tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
                    create_document(title, category, tags_list, content)
                    st.success(f"문서 '{file_name}'이 수정되었습니다.")
            else:
                st.info("수정할 문서가 없습니다.")

        elif action == "삭제":
            st.subheader("문서 삭제")
            if metadata:
                file_name = st.selectbox("삭제할 문서 선택", list(metadata.keys()))
                if st.button("문서 삭제"):
                    delete_document(file_name)
                    st.success(f"문서 '{file_name}'이 삭제되었습니다.")
            else:
                st.info("삭제할 문서가 없습니다.")

    ################################
    # 템플릿 관리
    ################################
    elif menu == "템플릿 관리":
        st.header("템플릿 관리")
        action = st.selectbox("작업 선택", ["보기", "추가", "수정", "삭제"])
        templates = load_json(TEMPLATES_FILE)

        if action == "보기":
            st.subheader("템플릿 보기")
            if templates:
                for tpl_id, tpl_data in templates.items():
                    st.write(f"**{tpl_id}:** {tpl_data['template_name']}")
                    with st.expander("내용 보기"):
                        st.code(tpl_data["content"], language="markdown")
            else:
                st.info("등록된 템플릿이 없습니다.")

        elif action == "추가":
            st.subheader("템플릿 추가")
            new_id = st.text_input("템플릿 ID (영어/숫자)")
            new_name = st.text_input("템플릿 이름")
            new_content = st.text_area("템플릿 내용", height=200)
            if st.button("템플릿 추가"):
                if new_id in templates:
                    st.error("이미 존재하는 템플릿 ID입니다.")
                else:
                    templates[new_id] = {"template_name": new_name, "content": new_content}
                    save_json(TEMPLATES_FILE, templates)
                    st.success(f"템플릿 '{new_id}' 추가 완료!")

        elif action == "수정":
            st.subheader("템플릿 수정")
            if templates:
                tpl_id = st.selectbox("수정할 템플릿 선택", list(templates.keys()))
                tpl_data = templates[tpl_id]
                updated_name = st.text_input("템플릿 이름", value=tpl_data["template_name"])
                updated_content = st.text_area("템플릿 내용", value=tpl_data["content"], height=200)
                if st.button("수정 완료"):
                    templates[tpl_id] = {"template_name": updated_name, "content": updated_content}
                    save_json(TEMPLATES_FILE, templates)
                    st.success(f"템플릿 '{tpl_id}' 수정 완료!")
            else:
                st.info("수정할 템플릿이 없습니다.")

        elif action == "삭제":
            st.subheader("템플릿 삭제")
            if templates:
                tpl_id = st.selectbox("삭제할 템플릿 선택", list(templates.keys()))
                if st.button("템플릿 삭제"):
                    del templates[tpl_id]
                    save_json(TEMPLATES_FILE, templates)
                    st.success(f"템플릿 '{tpl_id}' 삭제 완료!")
            else:
                st.info("삭제할 템플릿이 없습니다.")

    ################################
    # 프롬프트 관리
    ################################
    elif menu == "프롬프트 관리":
        st.header("프롬프트 관리")
        action = st.selectbox("작업 선택", ["보기", "추가", "수정", "삭제"])
        prompts = load_json(PROMPTS_FILE)

        if action == "보기":
            st.subheader("프롬프트 보기")
            if prompts:
                for prompt_id, prompt_data in prompts.items():
                    st.write(f"**{prompt_id}:** {prompt_data}")
            else:
                st.info("등록된 프롬프트가 없습니다.")

        elif action == "추가":
            st.subheader("프롬프트 추가")
            prompt_id = st.text_input("프롬프트 ID")
            prompt_text = st.text_area("프롬프트 내용", height=200)
            if st.button("프롬프트 추가"):
                if prompt_id in prompts:
                    st.error("이미 존재하는 프롬프트 ID입니다.")
                else:
                    prompts[prompt_id] = prompt_text
                    save_json(PROMPTS_FILE, prompts)
                    st.success(f"프롬프트 '{prompt_id}' 추가 완료!")

        elif action == "수정":
            st.subheader("프롬프트 수정")
            if prompts:
                prompt_id = st.selectbox("수정할 프롬프트 선택", list(prompts.keys()))
                updated_text = st.text_area("프롬프트 내용", value=prompts[prompt_id], height=200)
                if st.button("수정 완료"):
                    prompts[prompt_id] = updated_text
                    save_json(PROMPTS_FILE, prompts)
                    st.success(f"프롬프트 '{prompt_id}' 수정 완료!")
            else:
                st.info("수정할 프롬프트가 없습니다.")

        elif action == "삭제":
            st.subheader("프롬프트 삭제")
            if prompts:
                prompt_id = st.selectbox("삭제할 프롬프트 선택", list(prompts.keys()))
                if st.button("프롬프트 삭제"):
                    del prompts[prompt_id]
                    save_json(PROMPTS_FILE, prompts)
                    st.success(f"프롬프트 '{prompt_id}' 삭제 완료!")
            else:
                st.info("삭제할 프롬프트가 없습니다.")

    ################################
    # 키워드 관리
    ################################
    elif menu == "키워드 관리":
        st.header("키워드 관리")
        action = st.selectbox("작업 선택", ["보기", "추가", "수정", "삭제"])
        keywords = load_json(KEYWORDS_FILE)

        if action == "보기":
            st.subheader("키워드 보기")
            if keywords:
                for keyword, description in keywords.items():
                    st.write(f"**{keyword}:** {description}")
            else:
                st.info("등록된 키워드가 없습니다.")

        elif action == "추가":
            st.subheader("키워드 추가")
            keyword = st.text_input("키워드")
            description = st.text_area("키워드 설명", height=100)
            if st.button("키워드 추가"):
                if keyword in keywords:
                    st.error("이미 존재하는 키워드입니다.")
                else:
                    keywords[keyword] = description
                    save_json(KEYWORDS_FILE, keywords)
                    st.success(f"키워드 '{keyword}' 추가 완료!")

        elif action == "수정":
            st.subheader("키워드 수정")
            if keywords:
                keyword = st.selectbox("수정할 키워드 선택", list(keywords.keys()))
                updated_description = st.text_area("키워드 설명", value=keywords[keyword], height=100)
                if st.button("수정 완료"):
                    keywords[keyword] = updated_description
                    save_json(KEYWORDS_FILE, keywords)
                    st.success(f"키워드 '{keyword}' 수정 완료!")
            else:
                st.info("수정할 키워드가 없습니다.")

        elif action == "삭제":
            st.subheader("키워드 삭제")
            if keywords:
                keyword = st.selectbox("삭제할 키워드 선택", list(keywords.keys()))
                if st.button("키워드 삭제"):
                    del keywords[keyword]
                    save_json(KEYWORDS_FILE, keywords)
                    st.success(f"키워드 '{keyword}' 삭제 완료!")
            else:
                st.info("삭제할 키워드가 없습니다.")

    ################################
    # MkDocs 관리
    ################################
    elif menu == "MkDocs 관리":
        st.header("MkDocs 관리")
        action = st.selectbox("작업 선택", ["빌드", "로컬 테스트", "배포"])

        if action == "빌드":
            st.subheader("MkDocs 빌드")
            if st.button("빌드 실행"):
                result = mkdocs_build()
                if "완료" in result:
                    st.success(result)
                else:
                    st.error(result)

        elif action == "로컬 테스트":
            st.subheader("MkDocs 로컬 테스트")
            if st.button("로컬 테스트 시작"):
                result = mkdocs_serve()
                if "시작" in result:
                    st.success(result)
                else:
                    st.error(result)

        elif action == "배포":
            st.subheader("MkDocs 배포")
            if st.button("배포 실행"):
                result = mkdocs_deploy()
                if "완료" in result:
                    st.success(result)
                else:
                    st.error(result)

    ################################
    # MERGED 파일 생성
    ################################
    elif menu == "MERGED 파일 생성":
        st.header("MERGED 파일 생성")
        
        # 사용자 입력 받기
        folder_path = st.text_input("Markdown 파일이 있는 폴더 경로 입력")
        output_file = st.text_input("병합된 파일 저장 경로 입력", "merged_overview.md")
        
        if st.button("MERGED 파일 생성"):
            if not folder_path or not output_file:
                st.error("폴더 경로와 저장 경로를 모두 입력하세요.")
            else:
                result = merge_md_files(folder_path, output_file)
                if "성공적으로 생성" in result:
                    st.success(result)
                else:
                    st.error(result)


if __name__ == "__main__":
    main()
