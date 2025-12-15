# Sistema de Inspeção Visual para Placas de Circuito Impresso (PCI)

Este repositório contém o código e os arquivos associados ao desenvolvimento de um sistema de inspeção visual de baixo custo para detecção de componentes ausentes em Placas de Circuito Impresso (PCIs). O sistema combina uma estrutura física dedicada para captura padronizada com algoritmos de visão computacional baseados na comparação entre uma placa de referência e a placa em inspeção.

## 📁 Estrutura do Repositório

- **/src**  
  Código-fonte em Python, incluindo:
  - captura de imagem
  - detecção de QR Codes
  - cálculo da homografia
  - retificação da placa
  - normalização fotométrica
  - comparação do canal *Cr*
  - geração da máscara binária

- **/cad**  
  Arquivos CAD da estrutura física utilizada para padronização do posicionamento da placa.  
  Disponíveis em:
  - **STL** — ideal para impressão 3D  
  - **STEP** — ideal para edição em softwares CAD (Fusion, SolidWorks, FreeCAD etc.)

- **/docs**  
  Arquivos complementares e documentação adicional (opcional).

## 🚀 Como Executar

### 1. Clone o repositório
```bash
git clone [https://github.com/joao1546/deteccao_falhas_montagem_smd.git]
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Execute o programa principal
```bash
python main.py
```

## 🧩 Arquivos CAD

A estrutura física utilizada no projeto — incluindo o suporte da câmera, o sistema de iluminação e a base ajustável da PCI — foi disponibilizada para permitir a reprodução completa da plataforma.

Você poderá:
- imprimir os modelos em **STL**
- editar os modelos em **STEP**
- adaptar a estrutura para novas aplicações

## 🤝 Contribuições

Contribuições são bem-vindas!  
Sinta-se livre para abrir *issues*, relatar bugs, sugerir melhorias ou enviar *pull requests*.
