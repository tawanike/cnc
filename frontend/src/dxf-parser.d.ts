declare module "dxf-parser" {
  interface LWPolylineVertex {
    x: number;
    y: number;
  }

  interface LWPolylineEntity {
    type: "LWPOLYLINE";
    vertices: LWPolylineVertex[];
    shape: boolean;
  }

  interface LineEntity {
    type: "LINE";
    vertices: [{ x: number; y: number }, { x: number; y: number }];
  }

  interface DxfEntity {
    type: string;
    vertices?: { x: number; y: number }[];
    shape?: boolean;
  }

  interface DxfResult {
    entities: DxfEntity[];
  }

  export default class DxfParser {
    parseSync(content: string): DxfResult;
  }
}
