import masterData from '../../../../lib/v2/master-data.mjs';
import { masterDataResponse } from '../_lib/respond';

export function GET(request) {
  return masterDataResponse(() => masterData.listAcademicPeriods(request.nextUrl.searchParams));
}
