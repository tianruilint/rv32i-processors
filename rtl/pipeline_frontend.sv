module pipeline_frontend (
    input  logic        clk,
    input  logic        reset,
    input  logic        stall,
    input  logic        redirect,
    input  logic [31:0] redirect_pc,
    input  logic [31:0] instr,
    output logic [31:0] current_pc,
    output logic        if_id_valid,
    output logic [31:0] if_id_instr,
    output logic [31:0] if_id_pc_plus_4,
    output logic [31:0] if_id_pc
);

    logic [31:0] pc;
    logic        if_id_valid_q;
    logic [31:0] if_id_pc_q;
    logic [31:0] if_id_instr_q;
    logic [31:0] if_id_pc_plus_4_q;

    assign current_pc = pc;
    assign if_id_valid = if_id_valid_q;
    assign if_id_instr = if_id_instr_q;
    assign if_id_pc_plus_4 = if_id_pc_plus_4_q;
    assign if_id_pc = if_id_pc_q;

    always_ff @(posedge clk) begin
        if (reset) begin
            pc <= 32'b0;
            if_id_valid_q <= 1'b0;
            if_id_pc_q <= 32'b0;
            if_id_instr_q <= 32'b0;
            if_id_pc_plus_4_q <= 32'b0;
        end
        else if (redirect) begin
            pc <= redirect_pc;
            if_id_valid_q <= 1'b0;
            if_id_pc_q <= 32'b0;
            if_id_instr_q <= 32'b0;
            if_id_pc_plus_4_q <= 32'b0;
        end
        else if (stall) begin
            pc <= pc;
            if_id_valid_q <= if_id_valid_q;
            if_id_pc_q <= if_id_pc_q;
            if_id_instr_q <= if_id_instr_q;
            if_id_pc_plus_4_q <= if_id_pc_plus_4_q;
        end
        else begin
            if_id_valid_q <= 1'b1;
            if_id_pc_q <= pc;
            if_id_instr_q <= instr;
            if_id_pc_plus_4_q <= pc + 32'd4;
            pc <= pc + 32'd4;
        end
    end

endmodule
