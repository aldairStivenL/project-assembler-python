import json

class InstructionEncoder:
    def __init__(self, json_file='instructions.json'):
        # Cargar las instrucciones desde un archivo JSON
        with open(json_file, 'r') as file:
            self.instructions = json.load(file)

    # Método para convertir los registros de 'x1' a '1', 'x2' a '2', etc.
    def parse_register(self, reg):
        if reg.startswith('x'):
            return int(reg[1:])  # extraemos el número del registro, e.g., 'x1' -> 1
        else:
            raise ValueError(f"Registro inválido: {reg}")

    # Codificación tipo R
    def encode_r_type(self, instr, rd, rs1, rs2):
        funct7, funct3, opcode = self.instructions['r_type_instructions'][instr]
        rd = format(self.parse_register(rd), '05b')  # Convertir registro a número binario
        rs1 = format(self.parse_register(rs1), '05b')
        rs2 = format(self.parse_register(rs2), '05b')
        return f"{funct7} {rs2} {rs1} {funct3} {rd} {opcode}"

    # Codificación tipo I
    def encode_i_type(self, instr, rd, rs1, imm):
        funct3, opcode = self.instructions['i_type_instructions'][instr]
        rd = format(self.parse_register(rd), '05b')
        rs1 = format(self.parse_register(rs1), '05b')
        imm = format(int(imm), '012b')  # Convertir el inmediato a 12 bits
        return f"{imm} {rs1} {funct3} {rd} {opcode}"

    # Codificación tipo S (almacenamiento)
# Codificación tipo S (Store)
    def encode_s_type(self, instr, rs1, rs2, imm):
        funct3, opcode = self.instructions['s_type_instructions'][instr]
        imm = int(imm)  # Convertir inmediato a entero
        imm_bin = format(imm, '012b')  # Convertir a 12 bits

        # Extraer partes del inmediato
        imm_11_5 = imm_bin[:7]   # Bits 11-5
        imm_4_0 = imm_bin[7:]    # Bits 4-0

        rs1_bin = format(self.parse_register(rs1), '05b')
        rs2_bin = format(self.parse_register(rs2), '05b')

        # Construcción del binario final
        instruction_bin = f"{imm_11_5} {rs2_bin} {rs1_bin} {funct3} {imm_4_0} {opcode}"
        
        return instruction_bin
    def encode_b_type(self, instr, rs1, rs2, imm):
        funct3, opcode = self.instructions['b_type_instructions'][instr]

        print(f"Valor recibido de imm: {imm} (tipo: {type(imm)})")  # Depuración
        imm = int(imm)  # Convertir a entero (venía como string)

        # ✅ Convertir los registros a números enteros
        rs1_int = self.parse_register(rs1)
        rs2_int = self.parse_register(rs2)

        # ✅ Si la condición se cumple, convertir a binario de 13 bits con complemento a dos
        imm_bin = format(imm & 0x1FFF, '013b')  # Asegura 13 bits

        print(f"Valor en binario de imm: {imm_bin}")  # Depuración

        # Extraer los bits correctamente según el formato B-Type de RISC-V
        imm_12  = imm_bin[0]      # Bit 12 (MSB - bit de signo)
        imm_10_5 = imm_bin[1:7]   # Bits 10-5
        imm_11   = imm_bin[7]     # Bit 11
        imm_4_1  = imm_bin[8:12]  # Bits 4-1

        # ✅ Convertir los registros a formato binario de 5 bits para la instrucción final
        rs1_bin = format(rs1_int, '05b')
        rs2_bin = format(rs2_int, '05b')

        # Ensamblar el formato final
        return f"{imm_12}{imm_10_5} {rs2_bin} {rs1_bin} {funct3} {imm_4_1}{imm_11} {opcode}"
            
    def encode_j_type(self, instr, rd, imm):
        if instr not in self.instructions['j_type_instructions']:
            raise ValueError(f"❌ ERROR: Instrucción '{instr}' no reconocida como tipo J (solo 'jal' o 'jalr').")

        opcode = self.instructions['j_type_instructions'][instr]

        # ✅ Convertir los registros y el inmediato a valores numéricos
        rd_int = self.parse_register(rd)

        try:
            imm = int(imm)  # Convertir el inmediato a entero
        except ValueError:
            raise ValueError(f"❌ ERROR: El inmediato '{imm}' no es un número válido.")

        # ✅ Verificar que el inmediato esté en el rango de 21 bits con signo (-1MiB a +1MiB)
        if not (-(1 << 20) <= imm < (1 << 20)):
            raise ValueError(f"❌ ERROR: El inmediato {imm} está fuera del rango permitido (-1048576 a 1048575).")

        # ✅ Convertir a binario de 21 bits con signo
        imm_bin = format(imm & 0x1FFFFF, '021b')  # Asegura 21 bits

        print(f"📌 Instrucción {instr}: rd={rd} ({rd_int}), imm={imm} ({imm_bin})")  # Depuración

        # ✅ Extraer los bits según el formato J-Type
        imm_20   = imm_bin[0]      # Bit 20 (MSB - bit de signo)
        imm_10_1 = imm_bin[1:11]   # Bits 10-1
        imm_11   = imm_bin[11]     # Bit 11
        imm_19_12 = imm_bin[12:20] # Bits 19-12

        # ✅ Convertir `rd` a 5 bits binarios
        rd_bin = format(rd_int, '05b')

        # Ensamblar el formato final J-Type
        return f"{imm_20}{imm_19_12}{imm_11}{imm_10_1} {rd_bin} {opcode}"


    # Codificación tipo U (inmediatos grandes)
    def encode_u_type(self, instr, rd, imm):
        if instr not in self.instructions['u_type_instructions']:
            raise ValueError(f"❌ ERROR: Instrucción '{instr}' no reconocida como tipo U (solo 'lui' o 'auipc').")
        
        opcode = self.instructions['u_type_instructions'][instr]
        rd_bin = format(self.parse_register(rd), '05b')

        # Validar que el inmediato sea un número entero
        try:
            imm = int(imm)
        except ValueError:
            raise ValueError(f"❌ ERROR: El inmediato '{imm}' no es un número válido (debe ser un entero).")
        
        # Validar el rango del inmediato (-524288 a 1048575)
        if not (-524288 <= imm < 1048576):  
            raise ValueError(f"❌ ERROR: El inmediato {imm} está fuera del rango permitido (-524288 a 1048575).")

        # Convertir a binario de 20 bits con signo (complemento a dos si es negativo)
        imm_bin = format(imm & 0xFFFFF, '020b')

        print(f"✅ Instrucción {instr} con rd={rd} y imm={imm} ({imm_bin})")  # Depuración
        
        # Retorna la instrucción en binario
        return f"{imm_bin} {rd_bin} {opcode}"

    # Método especial para las instrucciones de carga tipo I
    def encode_i_type_load(self, instr, rd, rs1, imm):
        if instr in self.instructions['i_type_load_instructions']:
            funct3, opcode = self.instructions['i_type_load_instructions'][instr]
            
            # Convertir inmediato a binario de 12 bits con signo
            imm_bin = format(int(imm) & 0xFFF, '012b')

            # Convertir registros a binario de 5 bits
            rd_bin = format(self.parse_register(rd), '05b')
            rs1_bin = format(self.parse_register(rs1), '05b')

            # Ensamblar el formato tipo I: imm[11:0] | rs1 | funct3 | rd | opcode
            instruction_bin = f"{imm_bin} {rs1_bin} {funct3} {rd_bin} {opcode}"

            return instruction_bin
    
