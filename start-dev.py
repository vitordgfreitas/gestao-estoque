"""
Script Python para iniciar backend e frontend simultaneamente
"""
import subprocess
import sys
import os
import time
from pathlib import Path

def main():
    print("=" * 50)
    print("  CRM Gestao Estoque - Iniciando...")
    print("=" * 50)
    print()
    
    # Caminhos
    backend_dir = Path("backend")
    frontend_dir = Path("frontend")
    
    # Verifica se os diretórios existem
    if not backend_dir.exists():
        print("❌ Erro: Diretório 'backend' não encontrado!")
        sys.exit(1)
    
    if not frontend_dir.exists():
        print("❌ Erro: Diretório 'frontend' não encontrado!")
        sys.exit(1)
    
    # Verifica e cria venv do backend se necessário
    venv_path = backend_dir / "venv"
    if not venv_path.exists():
        print("Criando ambiente virtual do backend...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], cwd=backend_dir)
    
    # Determina o executável Python do venv
    if sys.platform == "win32":
        python_exe = venv_path / "Scripts" / "python.exe"
        activate_script = venv_path / "Scripts" / "activate.bat"
    else:
        python_exe = venv_path / "bin" / "python"
        activate_script = venv_path / "bin" / "activate"
    
    if not python_exe.exists():
        print("❌ Erro: Ambiente virtual do backend não está configurado corretamente!")
        sys.exit(1)
    
    # Inicia o backend
    print("Iniciando Backend (FastAPI)...")
    backend_process = subprocess.Popen(
        [str(python_exe), "run.py"],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Aguarda backend iniciar
    print("Aguardando backend iniciar...")
    time.sleep(3)
    
    # Verifica se o backend está rodando
    if backend_process.poll() is not None:
        print("❌ Erro: Backend não iniciou corretamente!")
        stdout, stderr = backend_process.communicate()
        print("STDOUT:", stdout.decode())
        print("STDERR:", stderr.decode())
        sys.exit(1)
    
    # Inicia o frontend
    print("Iniciando Frontend (React)...")
    
    # Verifica se node_modules existe
    node_modules = frontend_dir / "node_modules"
    if not node_modules.exists():
        print("Instalando dependências do frontend...")
        if sys.platform == "win32":
            subprocess.run(["npm", "install"], cwd=frontend_dir, shell=True)
        else:
            subprocess.run(["npm", "install"], cwd=frontend_dir)
    
    # Inicia o frontend
    # No Windows, precisa usar shell=True para encontrar npm no PATH
    if sys.platform == "win32":
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )
    else:
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    
    print()
    print("=" * 50)
    print("  Ambos os servidores estão rodando!")
    print("=" * 50)
    print("  Backend:  http://localhost:8000")
    print("  Frontend: http://localhost:5173")
    print()
    print("Pressione Ctrl+C para parar ambos os servidores...")
    print()
    
    try:
        # Aguarda até que um dos processos termine
        while True:
            if backend_process.poll() is not None:
                print("❌ Backend parou!")
                break
            if frontend_process.poll() is not None:
                print("❌ Frontend parou!")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nParando servidores...")
        backend_process.terminate()
        frontend_process.terminate()
        backend_process.wait()
        frontend_process.wait()
        print("Servidores parados.")

if __name__ == "__main__":
    main()
