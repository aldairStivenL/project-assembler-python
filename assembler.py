import sys
from parser import InstructionParser

def remove_comments(line):
    return line.split('#')[0].strip()  # Elimina comentarios y espacios en blanco

def first_pass(input_file):
    labels = {}
    address_counter = 0
    
    with open(input_file, 'r') as infile:
        for line in infile:
            line = remove_comments(line)
            if not line:
                continue
            if line.endswith(':'):  # Detectar etiquetas
                label = line[:-1]  # Remover los dos puntos
                labels[label] = address_counter
            else:
                address_counter += 4  # Cada instrucción ocupa 4 bytes
    
    print("Diccionario de etiquetas:")
    for label, address in labels.items():
        print(f"{label}: {address}")
    
    return labels

def process_file(input_file, output_file):
    labels = first_pass(input_file)  # Primera pasada para encontrar etiquetas
    parser = InstructionParser('instructions.json')

    branch_instructions = {'b', 'beq', 'bne', 'blt', 'bge'}  # Instrucciones tipo B
    
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        address_counter = 0
        for line in infile:
            line = remove_comments(line)
            if not line or line.endswith(':'):  # Ignorar líneas vacías o etiquetas
                continue
            try:
                parts = line.split()  # Separar la instrucción y sus operandos
                instr = parts[0].lower()  # Normalizar a minúsculas
                
                if instr in branch_instructions and len(parts) > 1:
                    label = parts[-1]  # Último elemento como etiqueta destino
                    if label in labels:
                        offset = (labels[label] - address_counter) // 2  # Calcular offset en palabras
                        parts[-1] = str(offset)  # Reemplazar etiqueta por el offset
                        line = ' '.join(parts)  # Reconstruir la línea
                else:
                    for label, address in labels.items():
                        line = line.replace(label, str(address))

                # Procesar la línea y obtener la representación binaria
                binary = parser.process_line(line)
                if binary:  # Solo escribe si hay un resultado válido
                    outfile.write(binary + "\n")
            except ValueError as e:
                outfile.write(f"Error en la línea: {line} - {str(e)}\n")
            
            address_counter += 4  # Sumar 4 a la dirección actual

if __name__ == "__main__":
    input_filename = "prog1.asm"
    output_filename = "prog1.bin"
    process_file(input_filename, output_filename)
