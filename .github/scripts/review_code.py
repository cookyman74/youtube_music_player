import openai
import os
import json
from git import Repo

# OpenAI API 키 가져오기
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_diff_content(file_path):
    """Git diff 명령을 사용하여 특정 파일의 변경된 부분을 가져오는 함수"""
    try:
        repo = Repo(".")
        origin = repo.remotes.origin
        origin.fetch()

        # 원격 브랜치와 로컬 HEAD 간의 diff를 가져옴
        diff_content = repo.git.diff('origin/main', 'HEAD', file_path)

        if diff_content:
            return diff_content
        else:
            return None
    except Exception as e:
        # JSON 호환 가능한 에러 메시지 반환
        return json.dumps({"error": f"Error getting diff for {file_path}: {str(e)}"})

def review_code(file_path, diff_content):
    """OpenAI API로 변경된 부분에 대한 코드 리뷰 요청"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            max_tokens=600,
            messages=[
                {"role": "system", "content": "You are a code reviewer. Always provide your feedback in Korean, regardless of the language of the question."},
                {"role": "user", "content": f"""
                Please review the following changes in the file:\n
                File: {file_path}\n
                Changes:\n{diff_content}\n
                Provide detailed feedback based on the following criteria:

                1. Are there any potential bugs introduced by these changes?
                2. Are there sections with duplicated code or opportunities for reusable modules?
                3. Does the code follow established coding conventions? Point out any inconsistencies.
                4. Provide refactoring suggestions to improve code quality, readability, and maintainability.
                5. Are there any performance issues? Suggest possible optimizations.
                6. Could any security vulnerabilities be introduced by these changes?
                7. Is the test coverage sufficient for these changes? If not, suggest additional test cases.
                8. Are the comments and documentation adequate? Point out anything unclear or needing further explanation.

                Only respond to relevant criteria and skip those that are unnecessary.
                Your response should be exclusively in Korean.
                """}
            ]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        # JSON 호환 가능한 에러 메시지 반환
        return json.dumps({"error": f"Error during review of {file_path}: {str(e)}"})

def get_changed_files():
    """원격 저장소와 로컬 저장소의 공통 조상을 기준으로 변경된 파일 목록을 가져오는 함수"""
    try:
        repo = Repo(".")

        # 원격 저장소 정보 갱신
        origin = repo.remotes.origin
        origin.fetch()

        merge_base = repo.git.merge_base('origin/main', 'HEAD')
        diff_index = repo.git.diff(merge_base, 'HEAD', '--name-only')

        # 변경된 파일 목록 출력 및 반환
        if not diff_index:
            print("No changes found between the last common ancestor and the current commit.")
            return []

        changed_files = diff_index.splitlines()
        return changed_files
    except Exception as e:
        print(json.dumps({"error": f"Error occurred while fetching changed files: {str(e)}"}))
        return []

def main():
    try:
        changed_files = get_changed_files()

        if not changed_files:
            output = {
                "summary": "변경된 코드가 없습니다.",
                "details": []
            }
            with open("review_output.json", "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            print("No code changes detected.")
            return

        review_summary = "코드 리뷰가 완료되었습니다. 세부 사항은 아래를 참조하세요."
        review_details = []

        for file in changed_files:
            if file.endswith(('.py', '.js', '.java', '.cpp', '.h')):
                diff_content = get_diff_content(file)
                if diff_content and not diff_content.startswith("Error"):
                    review = review_code(file, diff_content)
                    review_details.append({"file": file, "comment": review})
                elif diff_content and diff_content.startswith("Error"):
                    # 오류 메시지도 JSON 형식으로 기록
                    review_details.append({"file": file, "comment": diff_content})

        output = {
            "summary": review_summary,
            "details": review_details
        }

        print(json.dumps(output, ensure_ascii=False, indent=2))
    except Exception as e:
        error_output = {
            "summary": "Error occurred during code review.",
            "details": [{"error": str(e)}]
        }
        print(json.dumps(error_output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
