"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Search,
  Eye,
  Trash2,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { formatDate, formatConfidence } from "@/lib/utils";

interface DiagnosisRow {
  id: number;
  filename: string;
  user: string;
  date: Date;
  model: string;
  prediction: string;
  confidence: number;
  status: string;
}

const mockData: DiagnosisRow[] = Array.from({ length: 25 }, (_, i) => ({
  id: i + 1,
  filename: `hoja_${String(i + 1).padStart(3, "0")}.jpg`,
  user: i % 3 === 0 ? "Admin" : `Cliente ${(i % 5) + 1}`,
  date: new Date(Date.now() - 86400000 * i),
  model: ["M1 - SVM", "M2 - Random Forest", "M3 - KNN"][i % 3],
  prediction: ["Sana", "Podredumbre Negra", "Esca", "Tizón de la Hoja"][i % 4],
  confidence: 0.85 + Math.random() * 0.14,
  status: i === 4 ? "processing" : "completed",
}));

const ITEMS_PER_PAGE = 8;

export default function AdminDiagnosticsPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [selectedDiag, setSelectedDiag] = useState<DiagnosisRow | null>(null);

  const filtered = mockData.filter((d) =>
    d.filename.toLowerCase().includes(search.toLowerCase())
  );
  const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE);
  const paged = filtered.slice(
    (page - 1) * ITEMS_PER_PAGE,
    page * ITEMS_PER_PAGE
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Diagnósticos</h2>
        <p className="text-muted-foreground">
          Administra todos los diagnósticos realizados en el sistema
        </p>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar por archivo..."
            className="pl-10"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Todos los Diagnósticos</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Archivo</TableHead>
                <TableHead>Usuario</TableHead>
                <TableHead>Fecha</TableHead>
                <TableHead>Modelo</TableHead>
                <TableHead>Predicción</TableHead>
                <TableHead>Confianza</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {paged.map((d) => (
                <TableRow key={d.id}>
                  <TableCell className="font-medium">{d.filename}</TableCell>
                  <TableCell>{d.user}</TableCell>
                  <TableCell>{formatDate(d.date)}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{d.model}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        d.prediction === "Sana" ? "success" : "destructive"
                      }
                    >
                      {d.prediction}
                    </Badge>
                  </TableCell>
                  <TableCell>{formatConfidence(d.confidence)}</TableCell>
                  <TableCell>
                    <Badge
                      variant={d.status === "completed" ? "success" : "warning"}
                    >
                      {d.status === "completed" ? "Completado" : "Procesando"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setSelectedDiag(d)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle>Diagnóstico #{d.id}</DialogTitle>
                            <DialogDescription>
                              Detalles del diagnóstico de {d.filename}
                            </DialogDescription>
                          </DialogHeader>
                          <div className="space-y-3">
                            <div className="grid grid-cols-2 gap-2 text-sm">
                              <span className="text-muted-foreground">Archivo:</span>
                              <span>{d.filename}</span>
                              <span className="text-muted-foreground">Usuario:</span>
                              <span>{d.user}</span>
                              <span className="text-muted-foreground">Modelo:</span>
                              <span>{d.model}</span>
                              <span className="text-muted-foreground">Predicción:</span>
                              <span>{d.prediction}</span>
                              <span className="text-muted-foreground">Confianza:</span>
                              <span>{formatConfidence(d.confidence)}</span>
                              <span className="text-muted-foreground">Fecha:</span>
                              <span>{formatDate(d.date)}</span>
                            </div>
                          </div>
                        </DialogContent>
                      </Dialog>
                      <Button variant="ghost" size="icon">
                        <RefreshCw className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" className="text-destructive">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          <div className="flex items-center justify-between mt-4">
            <p className="text-sm text-muted-foreground">
              Página {page} de {totalPages}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
